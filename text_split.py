

document = ' '.join(lines)
texts = text_splitter.split_text(document)

print(len(texts[0]))