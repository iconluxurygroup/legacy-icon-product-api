![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
[![Application Test | Github Actions](https://github.com/nikiconluxury/icon-product-api/actions/workflows/devops.yml/badge.svg)](https://github.com/nikiconluxury/icon-product-api/actions/workflows/devops.yml)


# icon-product-api

1. Create python virtual enviroment 'python3 -m venv .venv'
2. Setup structure files 'Makefile, 'requirements.txt' , 'main.py, 'Dockerfile, 'mylib/__init__.py', 
3. Populate 'Makefile'
4. Setup continuous integration
5. Build cli using Python Fire Library './cli-fire.py' to test logic
6. Write tests and update make file and CI
7. Setup 'Dockerfile' and 'docker-compose.yml'
8. build, test, deploy
7. Read API key from variable, later dotenv variable
8. Skip products that have images (option)
# sam


Issues:


1. look into having it fetch resources on web storage

2. I've caught Currency coming back as $ lets unify it to USD
3. Filter values should be loaded dynamically: self.filtered_urls = self.filter_urls_by_currency(['/us/','/en-us/','/us-en/','/us.','modesens.com/product','fwrd.com/mobile/product','marcjacobs.com/default/'], self.filtered_urls)
4. whitelist urls to be fetched dynamically
5. Pls review all functions and make sure there is a unified format for returning Null. None, 'Error' Lets pick one and use it. Most likely None to ease contional statements. 
8. 'approved_seller_list' needs to be read from web
9. See what kind of exceptions are occuring and be more specific 'tasks/classes_and_utility.py:191:19:', 'tasks/classes_and_utility.py:310:15:' 'Catching too general exception Exception (broad-exception-caught)'
#Review 


PRIORITY:
0. Refactor the process of parsing html. Needs to be easy to add new Parser class and implement into its logic flow. Lets discuss this first.
- Search logic, setting type that will determine what is considered an acceptable result. Ex. Image search type will take modesens any main image seller does not matter.  
- Variation, allow for a bypass brand settings and just create variations based on article model color input
- Currency support, user will choose US or EURO, need to provide logical support for this. for both the scraperapi to choose country and filter for urls as they are coming in from google results. Confirm there arent more dependancies.


