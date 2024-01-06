import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk
import time
import openai
import pandas as pd
from nltk.tokenize import word_tokenize
nltk.download('punkt')

with open('./modelo_svc.pkl', 'rb') as model_file:
        modelo_svc = pickle.load(model_file)

with open('./vectorizer.pkl', 'rb') as vec_file:
        vectorizer = pickle.load(vec_file)

with open('./categories_map.pkl', 'rb') as vec_file:
        category_map = pickle.load(vec_file)

with open('./stopwords_es.pkl', 'rb') as sw_file:
        stopwords_es = pickle.load(sw_file)

openai.api_key = "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"

def extract_content(paragraphs):
    content = '\n'.join([''.join(p.xpath('.//text()').getall()) for p in paragraphs])
    content = content.replace('\xa0', ' ').replace('\r\n', '\n')
    return content


def repair_item(item):
    if all([v is not None or v != '' for v in item.values()]):
        return item
    return None


def remove_nodes(root, selectors):
    for selector in selectors:
        element = root.css(selector)
        if element:
            element = element[0].root
            element.getparent().remove(element)
        
    return root

def clean_text(text):
        text = ''.join(text)
        text = text.replace("\n", '')
        text = ''.join(text)
        return text.strip()

def predict_categories(text):
        # Asegúrate de tener 'vectorizer' y 'category_map' definidos adecuadamente
        nuevo_texto_tfidf = vectorizer.transform([text])
        probabilidades = modelo_svc.predict_proba(nuevo_texto_tfidf)
        sort_probabilidades = [sorted(enumerate(prob), key=lambda x: -x[1])[:4] for prob in probabilidades][0]
        first_cat, first_pred = sort_probabilidades[0]
        sec_cat, sec_pred = sort_probabilidades[1]
        first_pred = round(first_pred, 2)
        sec_pred = round(sec_pred, 2)
        if first_pred >= 0.65:
            return category_map[first_cat], first_pred, '', 0.0
        else:
            return category_map[first_cat], first_pred, category_map[sec_cat], sec_pred
        

def preprocesar_texto(texto):
    if isinstance(texto, str):

        # Tokenizar el texto en palabras
        palabras = word_tokenize(texto.lower())  # Convertir a minúsculas para uniformidad

        # Eliminar signos de puntuación y números
        palabras = [palabra for palabra in palabras if palabra.isalpha()]

        # Eliminar stopwords
        palabras = [palabra for palabra in palabras if palabra not in stopwords_es]

        # Unir las palabras nuevamente en una cadena
        texto_limpio = ' '.join(palabras)

        return texto_limpio
    
def isGORE(text):
    text = text.lower()
    lista_palabras = ['gore de la rm',
                'gore metropolitano',
                'gore de santiago',
                'gore de la region metropolitana',
                'gobierno regional metropolitano de santiago',
                'gobierno regional metropolitano',
                'gobernador de la region metropolitana',
                'gobierno metropolitano',
                'gobernador orrego',
                'claudio orrego',
                'gobernador claudio orrego',
                'gobernador de la rm']

    if isinstance(text, str):
        if any(palabra in text for palabra in lista_palabras):
            return 1
        else:
            return 0
    return 0
    

categorias = ["Seguridad", "Medioambiente", "Política", "Movilidad", "Economía", "Salud", "Educación", "Deportes", "Internacional", "Entretenimiento", "Desastres Naturales"]


def getCategories(article, temperature = 0.5):
    prompt_instruction = f"""Eres un Clasificador de noticias que categoriza entre 11 categorías articulos noticiosos. Estas son las categorías que usas para clasificar con una breve definición:
                      Seguridad, Medioambiente, Política, Movilidad, Economía, Salud, Educación, Deportes, Internacional, Entretenimiento, Desastres Naturales"""

    prompt_base = f"""Para el siguiente artículo dado, por favor declara a cual de las 11 categorías corresponde la noticia. Si la noticia no corresponde a ninguna de las categorías retorna "Otro". Si la noticia corresponde a dos categorías retorna ambas categorías.
                  La salida para una sola categoría es solo la categoría encontrada, ej: Seguridad
                  La salida para dos categorías son las dos categorias encontradas separadas por un ";" en orden de importancia, ej: Movilidad;Medioambiente"""
    try:
        response = openai.chat.completions.create(#openai.ChatCompletion.create(
        model = "gpt-3.5-turbo",
        messages = [{"role": "user",
                    "content": prompt_instruction + prompt_base + article}],
        temperature = temperature # 0.5
        )
        answer = response.choices[0].message.content

        return answer

    except openai.APIError as e:
      #Handle API error here, e.g. retry or log
      print(f"OpenAI API returned an API Error: {e}")
      time.sleep(60)
      return None

    except openai.APIConnectionError as e:
      #Handle connection error here
      print(f"Failed to connect to OpenAI API: {e}")
      time.sleep(60)
      return None

    except openai.RateLimitError as e:
      #Handle rate limit error (we recommend using exponential backoff)
      print(f"OpenAI API request exceeded rate limit: {e}")
      time.sleep(60)
      return None
    
def setCategories(text):
    cont = 0
    if isinstance(text, str):
        while True:
            cont += 1
            if cont > 2:
                 return None, None
            tag = getCategories(text[:7500], temperature=0.5)
            if tag != None:
                break
        if ";" in tag:
            cats = tag.split(";")
            cats = cats[:2]
            if cats[0] not in categorias:
                cats[0] = "Otro"
            if cats[1] not in categorias:
                cats[1] = "Otro"
            if cats[0] == cats[1]:
                cats[1] = None
            return cats[0].strip(), cats[1].strip()
        else:
            if tag.strip() not in categorias:
                tag = "Otro"
            return tag.strip(), None
