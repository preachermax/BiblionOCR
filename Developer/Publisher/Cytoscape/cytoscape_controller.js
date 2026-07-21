async function loadGraph(){


    const response =
        await fetch(
            "launch_graph.json"
        );


    const elements =
        await response.json();



    const cy =
        cytoscape({

            container:
                document.getElementById("cy"),


            elements:
                elements,


            layout:
            {
                name:
                    "breadthfirst",

                directed:
                    true,

                padding:
                    40
            },


            style:
            [

                {
                    selector:"node",

                    style:
                    {

                        "label":
                            "data(label)",

                        "text-valign":
                            "center",

                        "text-halign":
                            "center",

                        "width":
                            90,

                        "height":
                            90
                    }
                },


                {
                    selector:"edge",

                    style:
                    {

                        "curve-style":
                            "bezier",

                        "target-arrow-shape":
                            "triangle"
                    }
                }


            ]

        });



    cy.on(
        "tap",
        "node",
        function(event)
        {

            const node =
                event.target;


            console.log(
                "Selected:",
                node.data("id")
            );


            console.log(
                "Help:",
                node.data("help")
            );


            /*
             Future:
                 emit signal to MyLauncher
                 through Qt WebChannel
            */

        }
    );


}


loadGraph();