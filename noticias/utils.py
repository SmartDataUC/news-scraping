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