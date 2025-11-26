# parse_tennis_score
This script gets the point log from tennisabstract.com and parse it into a structured CSV file.

# How to use
1. Construct the environment from requirements.txt:
   ```
   pip install -r requirements.txt
   ```
2. Run the main script:
   ```
   python main.py
   ```
3. Input the URL of the tennis match page on tennisabstract.com when prompted.  
4. Input the desired output CSV file name when prompted.
5. The parsed data will be saved in the specified CSV file.

# Example
```
Enter the url: https://www.tennisabstract.com/charting/20251113-M-Tour_Finals-RR-Carlos_Alcaraz-Lorenzo_Musetti.html
Enter the output file name (must end with .csv): test_output.csv
```
The parsed data will be saved in `test_output.csv`.

# Note
- Ensure that the output file name ends with `.csv` to avoid errors.

# Explanation of the output columns
- `Server`, `Sets`, `Games`, `Points`, `info`: Original columns from tennisabstract.com.
- `left_win`: Indicates if the left player won the point (1 for win, 0 for loss).
- `serve`: Indicates which direction the serve was made.
- - T represents "serve down the T"
- - W represents "serve wide"
- - B represents "serve to body"
- `fault`: Indicates how the fault occurred.
- - L represents long
- - W represents wide
- - N represents net
- `is_first`: Indicates if it was a first serve (1 for first serve, 0 for second serve)