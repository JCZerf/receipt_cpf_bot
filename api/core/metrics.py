from prometheus_client import Counter, Histogram

cpf_queries_total = Counter(
    "cpf_queries_total",
    "Total de consultas de CPF realizadas",
    ["status"],
)

cpf_query_duration_seconds = Histogram(
    "cpf_query_duration_seconds",
    "Duracao da consulta de CPF em segundos",
)

captcha_result_total = Counter(
    "captcha_result_total",
    "Resultado do captcha conforme aceito ou rejeitado pela fonte",
    ["result"],
)

captcha_rounds_total = Histogram(
    "captcha_rounds_total",
    "Rodadas de desafio ate o captcha ser aceito",
    buckets=(1, 2, 3, 4, 5, 7, 10, 15, 20),
)
