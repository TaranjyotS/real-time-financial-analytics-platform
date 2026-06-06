from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum as spark_sum

spark = SparkSession.builder.appName("portfolio-aggregation").getOrCreate()
transactions = spark.read.option("header", True).csv("/data/transactions.csv")
summary = transactions.groupBy("portfolio_id").agg(spark_sum(col("amount").cast("double")).alias("total_transaction_amount"))
summary.write.mode("overwrite").json("/data/output/portfolio_summary")
spark.stop()
