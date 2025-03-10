from bs4 import BeautifulSoup

# Sample HTML content
html_content = """
<html>
  <head><title>Test Page</title></head>
  <body>
    <h1>Welcome to the Test Page</h1>
    <p>This is a <a href="https://example.com">link</a> to example.com.</p>
    <ul>
      <li>Item 1</li>
      <li>Item 2</li>
      <li>Item 3</li>
    </ul>
  </body>
</html>
"""

# Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(html_content, 'html.parser')

# Extract and print the title of the page
title = soup.title.string
print(f"Title: {title}")

# Extract and print the text of the first <h1> tag
h1 = soup.h1.string
print(f"Header: {h1}")

# Extract and print the href attribute of the first <a> tag
link = soup.a['href']
print(f"Link: {link}")

# Extract and print all the list items
items = soup.find_all('li')
print("List Items:")
for item in items:
    print(f" - {item.string}")


