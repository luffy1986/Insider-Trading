# Insider-Trading
To track insider trading by scraping SEC website and Yahoo finance

-h, --help            show this help message and exit

-days DAYS, --days DAYS
                      To specify how many days from today do you want to look for insider trading. Default value is 30 days

-processes PROCESSES, --processes PROCESSES
                      To specify how many processes to run parallely. Specifying a large value may slow down your machine. Default value is 10.

-filename FILENAME, --filename FILENAME
                      To specify a filename for xlsx. Default name is insider_trading

-stocklist STOCKLIST, --stocklist STOCKLIST
                      To specify a list of stocks on which to see insider trading. Default list of stocks will be based out of yahoo finance
                      using yahoo_fin python library.

-insidersales INSIDERSALES, --insidersales INSIDERSALES
                        To specify if you want to see insider selling in the stocks. Default is 0

-insiderbuys INSIDERBUYS, --insiderbuys INSIDERBUYS
                      To specify if you want to see insider buying in the stocks. Default is 1

-mktcap MKTCAP, --mktcap MKTCAP
                      To specify the minimum market cap as a criteria for insider trading. You can pass values like
                      1.5B, 100M. Default is 0

-startdate STARTDATE, --startdate STARTDATE
                      To specify the starting date to track insider buying. The format is YYYY-MM-DD for eg: 2020-12-21

-enddate ENDDATE, --enddate ENDDATE
                      To specify the end date to track insider buying. The format is YYY-MM-DD for eg: 2020-12-21
