"""
ui_tutorial_generator.py

Generate static HTML tutorials from Qt Designer .ui files.

Designed for:
    BiblionOCR
    MyLauncher
    MyServer
    MyReader
    etc.

The .ui file remains the source of truth.
"""

from pathlib import Path
import xml.etree.ElementTree as ET
import json
import shutil


class UITutorialGenerator:
    """
    Convert Qt Designer UI metadata into a static HTML tutorial.

    Expected Qt Designer custom properties:

        tutorial.enabled = true
        tutorial.title = "MyServer"
        tutorial.help = "Loads and manages projects"
        tutorial.image = "images/myserver.png"
        tutorial.order = 1

    These should be attached to QPushButton widgets.
    """

    def __init__(self, ui_file, output_dir):

        self.ui_file = Path(ui_file)
        self.output_dir = Path(output_dir)

        self.widgets = []
        self.html_dir = self.output_dir / "tutorial"
        self.image_dir = self.html_dir / "images"


    def parse_ui(self):
        """
        Read Qt Designer XML.
        """

        tree = ET.parse(self.ui_file)
        root = tree.getroot()

        for widget in root.findall(".//widget"):

            classname = widget.attrib.get("class")
            name = widget.attrib.get("name")

            if classname != "QPushButton":
                continue

            properties = {}

            for prop in widget.findall("property"):

                prop_name = prop.attrib.get("name")

                text = prop.find("string")
                number = prop.find("number")
                boolean = prop.find("bool")

                if text is not None:
                    properties[prop_name] = text.text

                elif number is not None:
                    properties[prop_name] = number.text

                elif boolean is not None:
                    properties[prop_name] = boolean.text


            if properties.get("tutorial.enabled") == "true":

                self.widgets.append(
                    {
                        "name": name,
                        "title": properties.get(
                            "tutorial.title",
                            name
                        ),

                        "help": properties.get(
                            "tutorial.help",
                            ""
                        ),

                        "image": properties.get(
                            "tutorial.image",
                            ""
                        ),

                        "order": int(
                            properties.get(
                                "tutorial.order",
                                999
                            )
                        )
                    }
                )


        self.widgets.sort(
            key=lambda x: x["order"]
        )

        return self.widgets



    def create_directories(self):

        self.html_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.image_dir.mkdir(
            parents=True,
            exist_ok=True
        )



    def write_data_file(self):

        data_file = self.html_dir / "tutorial.json"

        with open(
            data_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                self.widgets,
                f,
                indent=4
            )


    def generate_html(self):

        html = """
<!DOCTYPE html>
<html>

<head>

<meta charset="utf-8">

<title>Biblion Tutorial</title>

<link rel="stylesheet" href="tutorial.css">

</head>


<body>


<div id="container">


<div id="menu">

</div>


<div id="content">

<h1 id="title"></h1>

<p id="help"></p>

<img id="image">


</div>


</div>


<script src="tutorial.js"></script>


</body>

</html>
"""

        with open(
            self.html_dir / "index.html",
            "w",
            encoding="utf-8"
        ) as f:

            f.write(html)



    def generate_javascript(self):

        js = """

let index = 0;


fetch("tutorial.json")

.then(r => r.json())

.then(data => {


const menu =
document.getElementById("menu");


const title =
document.getElementById("title");


const help =
document.getElementById("help");


const image =
document.getElementById("image");



data.forEach((item,i)=>{


let button =
document.createElement("div");


button.className="module";


button.innerText=item.title;


button.onclick=()=>show(i);


menu.appendChild(button);


});



function show(i){


let item=data[i];


title.innerText=item.title;


help.innerText=item.help;


image.src=item.image;


document
.querySelectorAll(".module")
.forEach(x=>x.classList.remove("active"));


document
.querySelectorAll(".module")[i]
.classList.add("active");


}



function animate(){


show(index);


index++;


if(index>=data.length)
    index=0;


}


animate();


setInterval(
animate,
4000
);



});

"""

        with open(
            self.html_dir / "tutorial.js",
            "w",
            encoding="utf-8"
        ) as f:

            f.write(js)



    def generate_css(self):

        css = """

body {
    font-family: Arial, sans-serif;
}


#container {

display:flex;

height:90vh;

}


#menu {

width:250px;

}


.module {

padding:15px;

cursor:pointer;

}



.active {

font-weight:bold;

}



#content {

padding:30px;

}


#image {

max-width:800px;

}

"""

        with open(
            self.html_dir / "tutorial.css",
            "w",
            encoding="utf-8"
        ) as f:

            f.write(css)



    def build(self):

        self.parse_ui()

        self.create_directories()

        self.write_data_file()

        self.generate_html()

        self.generate_javascript()

        self.generate_css()

        return self.html_dir