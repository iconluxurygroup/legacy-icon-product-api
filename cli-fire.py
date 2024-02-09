#!/usr/bin/env python
import fire
from mylib import logic
from tasks.celery_back_tasks import create_task

class CLI:
    def __init__(self):
        self.logic = logic
    ###FORMAT CLI ARGS
    @staticmethod
    def format_arguments(brand : str, sku : str):
        return [brand,sku]
                 

    def create_task(self, brand, sku):
        formatted_data = self.format_arguments(brand, sku)
        create_task(formatted_data)

if __name__ == "__main__":
    fire.Fire(CLI)
