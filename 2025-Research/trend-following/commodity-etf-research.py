import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf


def write_data_to_csv(filename: str, data) -> bool:
    try:
        data.to_csv(filename)
    except Exception as e:
        print(f"Exception: {e}")
        return False

    return True


def main() -> None:
    etfs = [
        "GLD",
        "SLV",
        "USO",
        "UNG",
        "PPLT",
        "DBB",
        "JJC",
        "CORN",
        "WEAT",
        "SOYB",
        "JO",
    ]

    data = yf.download(etfs)
    res = write_data_to_csv("./commodity-data.csv", data)
    print(res)


if __name__ == "__main__":
    main()
