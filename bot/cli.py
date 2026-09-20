import argparse
import asyncio

from bot.browser import open_page
from bot.captcha import auto_solver
from bot.extract import extract_result
from bot.fetch import fetch_result_html
from bot.logging_config import configure_logging
from bot.models import CpfQuery


async def main() -> None:
    configure_logging()

    parser = argparse.ArgumentParser(description="Query CPF registration status")
    parser.add_argument("cpf")
    parser.add_argument("birth_date", help="ddmmyyyy")
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()

    query = CpfQuery(cpf=args.cpf, birth_date=args.birth_date)
    async with open_page(headless=args.headless) as page:
        html = await fetch_result_html(page, query, captcha_solver=auto_solver)
    result = extract_result(html)
    print(result.record if result.record else result.message)


if __name__ == "__main__":
    asyncio.run(main())
