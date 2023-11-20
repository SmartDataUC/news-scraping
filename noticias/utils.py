import pickle
from sklearn.feature_extraction.text import TfidfVectorizer

with open('./modelo_svc.pkl', 'rb') as model_file:
        modelo_svc = pickle.load(model_file)

with open('./vectorizer.pkl', 'rb') as vec_file:
        vectorizer = pickle.load(vec_file)

with open('./categories_map.pkl', 'rb') as vec_file:
        category_map = pickle.load(vec_file)

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