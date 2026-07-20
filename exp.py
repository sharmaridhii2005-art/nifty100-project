from src.etl.normaliser import normalize_year, normalize_ticker

print("Testing normalize_year()")
print(normalize_year("FY22"))
print(normalize_year("2022"))
print(normalize_year("2022.0"))

print("\nTesting normalize_ticker()")
print(normalize_ticker("tcs"))
print(normalize_ticker("TCS.NS"))
print(normalize_ticker("infy.bo"))