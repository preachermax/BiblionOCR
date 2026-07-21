async function loadGraph(){


    const response =
        await fetch(
            "launch_graph.json"
        );


    const payload =
        await response.json();


    const elements =
        buildElements(payload);



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

    window.cy = cy;



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

            showNodeInfo(node);


            /*
             Future:
                 emit signal to MyLauncher
                 through Qt WebChannel
            */

        }
    );


}


function buildElements(payload){

    if (Array.isArray(payload)) {
        return payload;
    }


    const nodes =
        (payload && Array.isArray(payload.nodes))
            ? payload.nodes
            : [];

    const edges =
        (payload && Array.isArray(payload.edges))
            ? payload.edges
            : [];


    const nodeElements =
        nodes.map(
            (node) => ({ data: node })
        );

    const edgeElements =
        edges.map(
            (edge) => ({ data: edge })
        );

    const nodeIds = new Set(
        nodeElements.map(
            (element) => element.data.id
        )
    );

    for (const edge of edgeElements) {
        const source = edge.data.source;
        const target = edge.data.target;

        if (source && !nodeIds.has(source)) {
            nodeElements.push({
                data: {
                    id: source,
                    label: source,
                    order: 0,
                    help: "",
                    animation: "idle",
                    script: "",
                }
            });
            nodeIds.add(source);
        }

        if (target && !nodeIds.has(target)) {
            nodeElements.push({
                data: {
                    id: target,
                    label: target,
                    order: 0,
                    help: "",
                    animation: "idle",
                    script: "",
                }
            });
            nodeIds.add(target);
        }
    }

    return nodeElements.concat(edgeElements);
}


function showNodeInfo(node){

    const nameEl = document.getElementById("node-name");
    const helpEl = document.getElementById("node-help");
    const orderEl = document.getElementById("node-order");

    if (!nameEl || !helpEl || !orderEl) {
        return;
    }

    nameEl.textContent = node.data("label") || node.data("id") || "";
    helpEl.textContent = node.data("help") || "(none)";
    orderEl.textContent = String(node.data("order") ?? "");
}


loadGraph();