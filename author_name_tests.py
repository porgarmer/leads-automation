# authors = [
#     "Oliver, Mary; Atwan, Robert", 
#     "William Strunk, Jr.; E. B. White",
#     "Larry Perry and other members of the Yearbook Staff",
#     "Bardsley, Clarence and Ernest Carlton",
#     "Tess Whitehurst,Llewellyn,James Kambos,Barbara Ardinger,B..",
#     "Julia Skinner & Robert Cook ( Editors )",
#     "Block, Adolphe et al.",
#     "Tucker, Harry",
#     "Barnett, Joseph",
#     "Michael Palin ; ( Photographer ) Basil Pao",
#     "Krzywicki, Ludwik & Schaff, Adam [editor]",
#     "Albornoz, Orlando",
#     '"Ginsberg, Morris"'
# ]

# filtered_authors = []

# def clean_author(author):
#         #remove trailing commas
#         author = author.strip('"').strip()
        
#         #remove anything after a quote
#         author = author.split('"')[0]
        
#         author = re.sub(r"\(.*?\)", "", author)
        
#         return author.strip()

# import re
# def is_single_author(author):
    
#     # obvous multi-author in
#     if re.search(r"\b(and|with|et al)\b|[&;]", author.lower()):
#         return False
    
#     name_pattern = re.findall(r"[A-Za-z]+,\s*[A-Za-z]+", author)
    
#     if len(name_pattern) > 1:
#         return False
    
#     words = author.split()
#     capitalized = [w for w in words if w and w[0].isupper()]
    
#     if len(capitalized) > 4:
#         return False
    
#     return True
    

# def is_lname_fname(author):
#     if author.count(",") != 1:
#         False
        
#     lname, fname = [p.strip() for p in author.split(",", 1)]
    
#     if not lname or not fname:
#         False
        
#     if len(fname.split()) > 3:
#         return False
    
#     return True
    
# def format_author_fname_lname(author):
    
#     # lname_fname will be a list like this = ["lname", "fname"]

#     lname, fname = [p.strip() for p in author.split(",", 1)]
#     return f"{fname} {lname}"
    
# filtered_authors = [a for a in authors if is_single_author(a)]

# formatted_authors = []
# for filtered_author in filtered_authors:
#     filtered_author = clean_author(author=filtered_author)
#     if is_lname_fname(filtered_author):
#         formatted_author = format_author_fname_lname(filtered_author).strip()
#         formatted_authors.append(formatted_author)

# print(formatted_authors)

address = "4103 Ivygrove Ln, Mason, OH 45040 +6"

print(address.split(" +"))