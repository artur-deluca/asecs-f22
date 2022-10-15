Artur Back de Luca
# Visualizing domestic collaboration within CS academia

The goal of this project is to analyze the collaboration between academics of Computer Science across universities within a given country.

As discussed in the chapter "The Science of Collaboration" of the book "The Science of Science", collaborations between institutions in academia have increased over the years in all disciplines.
However, the proportions between international and domestic collaborations vary across countries.

Motivated by this, we propose to further inspect the dynamics of collaboration in different countries within the field of Computer Science.

### How to use
```bash
# first install the dependencies
pip install -r ./requirements.txt 

# run jupyter and go to report.ipynb
jupyter notebook
```
The files extracted from DBLP and CSRankings are already located in the `data/` directory.
In case you want to extract the data by yourself, you must set up Selenium with a webdriver such as [Firefox](https://www.youtube.com/watch?v=9ye7srmAnMU).
Once that is done, run `python asecs/crawler.py`
