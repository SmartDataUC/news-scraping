# Scraping de Medios de Comuniación 📰
En este repositorio se encuentran los archivos necesarios para descargar noticias de distintos medios chilenos `[latercera, eldinamo, elmostrador, biobiochile, cnnchile, theclinic, adnradio, publimetro]`

La principal librería para realizar el scraping es [scrapy](https://scrapy.org/), que permite crear distintos archivos (spiders) para cada sitio web y mantiene el flujo de los datos creando distintos pipelines.
## Instalación
Instalar los requerimientos necesarios:
```
pip install -r requirements.txt
```
Ver los spiders disponibles (uno por cada medio):
```
scrapy list
```
Ejecutar un spider parituclar:
```
scrapy crawl latercera
```
