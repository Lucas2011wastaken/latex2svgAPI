# latex2svgAPI
a simple python script that allows user to compile LaTeX and get a SVG output via API.

recommended platform: Linux
> for its fast LaTeX compilation

**IMPORTANT: THIS API REQUIRES THE FOLLOWING APPLICATIONS INSTALLED ON THE SERVER**
- [xelatex](https://tug.org/texlive/)
- [pdf2svg](https://github.com/dawbarton/pdf2svg)


# calling the API

method: GET

|Parameter|type|comments|
|:--:|:--:|:---|
|`token`|str|a string to distinguish diffrent users|
|`latex`|str|the code you need to compile|
|`border`|float|(OPTIONAL)the border control for standalone, 0 by default|

# undone checklist

- [ ] ComPileTwice: for some circumstances that requires a second compilation. (e.g. macro, polymer)