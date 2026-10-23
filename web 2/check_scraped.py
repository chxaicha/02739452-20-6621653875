import pandas as pd


df = pd.read_csv("scraped_books.csv")


print("จำนวนข้อมูลทั้งหมด:", len(df))

print("\nจำนวนข้อมูลซ้ำ:")
print(df.duplicated().sum())

print("\nจำนวนค่าว่างแต่ละ column:")
print(df.isnull().sum())

print("\nตัวอย่างข้อมูล 5 รายการ:")
print(df.head())

print("\nข้อมูลแต่ละ column:")
print(df.dtypes)

print("\nRating:")
print(df["rating"].value_counts().sort_index())

print("\nราคาต่ำสุด:", df["price"].min())
print("ราคาสูงสุด:", df["price"].max())