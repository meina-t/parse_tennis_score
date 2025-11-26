import pandas as pd
import numpy as np
import re
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

def parse_tennis_table(url, file_name):
    df = get_table(url)
    if df is not None:
        try:
            df.rename(columns={df.columns[4]: 'info'}, inplace=True)
            df["left_win"] = score_to_left_win(df['Points'])
            service_columns = ['first', 'first_f', 'second', 'second_f']
            df[service_columns] = df['info'].apply(info_parser).apply(pd.Series)
            df = split_second_rows(df)
        except Exception as e:
            print(f"Error processing DataFrame: {e}")
        try:
            df.to_csv(file_name, index=False)
        except Exception as e:
            print(f"Error saving DataFrame to CSV: {e}")
    else:
        print("Failed to retrieve table.")

def get_table(url):
    try:
        print(f"Accessing URL: {url}")
        driver = webdriver.Chrome()
        driver.get(url)
    except Exception as e:
        print(f"Error accessing {url}: {e}")
        return None

    try:
        print(f"Expanding table on URL: {url}")
        id = "pointlog"
        button_selector = (By.ID, id)
        WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(button_selector)
        )
        button = driver.find_element(*button_selector)
        button.click()
    except Exception as e:
        print(f"Error expanding table on {url}: {e}")
        driver.quit()
        return None
    
    try:
        print(f"Reading table from URL: {url}")
        page_source = driver.page_source
        tables = pd.read_html(page_source)
        df = tables[-1]
    except Exception as e:
        print(f"Error reading table from {url}: {e}")
        driver.quit()
        return None
    driver.quit()
    return df

def score_to_left_win(score_series: pd.Series) -> pd.Series:
    """
    Args:
        score_series
    Returns:
        レフト側がポイントを獲得した場合は True、それ以外は False のブール値Series。
    """
    # Shift(-1)を使用して、各行に「次のスコア」を併記します
    scores_df = pd.DataFrame({
        'current_score': score_series,
        'next_score': score_series.shift(-1)
    })
    # 不要な空白や特殊文字を削除
    scores_df['current_score'] = scores_df['current_score'].str.replace(' ', '', regex=False).str.replace('‑', '-', regex=False)
    scores_df['next_score'] = scores_df['next_score'].str.replace(' ', '', regex=False).str.replace('‑', '-', regex=False)
    
    score_map = {'0': 0, '15': 1, '30': 2, '40': 3, 'AD': 4}

    def is_left_win(current_score, next_score):
        """
        現在のスコアと次のスコアを比較し、レフト側が勝ったかを返す
        """
        #　空行(セット間)の場合はNoneを返す
        if pd.isna(current_score):
            return None
        # セット終了時
        if pd.isna(next_score):
            if current_score == '40-0' or \
               current_score == '40-15' or \
               current_score == '40-30' or \
               current_score == 'AD-40':
                return True # レフト側の勝利でゲーム終了
            elif current_score == '0-40' or \
                 current_score == '15-40' or \
                 current_score == '30-40' or \
                 current_score == '40-AD':
                return False # ライト側の勝利でゲーム終了
            else:
                return None # error case

        # 通常ポイント
        try:
            L_curr, R_curr = current_score.split('-')
            L_next, R_next = next_score.split('-')
            
            # 数値に変換 (存在しないスコア表記は例外でFalse)
            L_curr_val = score_map.get(L_curr)
            R_curr_val = score_map.get(R_curr)
            L_next_val = score_map.get(L_next)
            R_next_val = score_map.get(R_next)

            # いずれかの値がNoneなら不正なスコアとしてFalse
            if None in [L_curr_val, R_curr_val, L_next_val, R_next_val]:
                return "None exists"
            
            diff_L = L_next_val - L_curr_val
            diff_R = R_next_val - R_curr_val
            
            # 通常のポイント増加
            if diff_L == 1 and diff_R == 0:
                return True
            # アドバンテージの解消
            if current_score == '40-AD' and next_score == '40-40':
                return True
            # その他(diff_R == 1, AD-40 -> 40-40, 40-40 -> 40-AD) はライトの勝利なので False
            return False

        except ValueError:
            return "fail to split or convert"
        except Exception:
            return "unexpected error"

    result_series = scores_df.apply(
        lambda row: is_left_win(row['current_score'], row['next_score']), 
        axis=1
    )
    return result_series

def info_parser(info):
    if not isinstance(info, str):
        return [None, None, None, None]
    def find_serve_patterns(info: str) -> tuple[str | None, str | None]:
        """
            T represents "serve down the T"
            W represents "serve wide"
            B represents "serve to body"
        """
        patterns = {
            "serve down the T": "T",
            "serve wide": "W",
            "serve to body": "B"
        }
        search_pattern = "|".join(re.escape(p) for p in patterns.keys())
        found_substrings = re.findall(search_pattern, info)
        
        results = [patterns[sub] for sub in found_substrings]
        
        first = results[0] if len(results) >= 1 else None
        second = results[1] if len(results) >= 2 else None

        return first, second
    def find_fault_patterns(info: str) -> tuple[str | None, str | None]:
        """
            L represents long
            W represents wide
            N represents net
        """
        patterns = {
            "fault (long)": "L",
            "fault (wide)": "W",
            "fault (net)": "N"
        }
        search_pattern = "|".join(re.escape(p) for p in patterns.keys())
        found_substrings = re.findall(search_pattern, info)
        
        results = [patterns[sub] for sub in found_substrings]
        
        first = results[0] if len(results) >= 1 else None
        second = results[1] if len(results) >= 2 else None

        return first, second
    serves = find_serve_patterns(info)
    faults = find_fault_patterns(info)
    return [serves[0], faults[0], serves[1], faults[1]]

def split_second_rows(df):
    df['is_first'] = pd.Series([True]*len(df))
    rows = []
    for _, row in df.iterrows():
        row_orig = row.copy()

        # second がある場合に分割する
        if pd.notnull(row['second']) or pd.notnull(row['second_f']):
            # 新しい行を作る
            row_new = row.copy()
            row_new['first'] = row['second']
            row_new['first_f'] = row['second_f']
            row_new['is_first'] = False

            rows.append(row_orig)
            rows.append(row_new)
        else:
            rows.append(row_orig)
    df = pd.DataFrame(rows)
    df.drop(columns=['second', 'second_f'], axis=1, inplace=True)
    df.rename(columns={'first': 'serve', 'first_f': 'fault'}, inplace=True)
    return df

if __name__ == "__main__":
    prompt = "Enter the url: "
    url = input(prompt)

    prompt = "Enter the output file name (e.g., output.csv): "
    while True:
        file_name = input(prompt)
        if file_name.endswith(".csv"):
            break
        print("Please enter a valid file name ending with .csv")
    parse_tennis_table(url, file_name=file_name)