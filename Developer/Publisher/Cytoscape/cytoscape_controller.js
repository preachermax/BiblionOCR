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
                            "data(node_label)",

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
            (node) => {
                const order =
                    node.order !== undefined
                        ? node.order
                        : "";
                const label =
                    node.label || node.id || "";
                return {
                    data: {
                        ...node,
                        node_label: `${label}${order !== "" ? ` (#${order})` : ""}`,
                    }
                };
            }
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
                    node_label: source,
                    order: 0,
                    help: "",
                    animation: "idle",
                    script: "",
                    ui_file: "",
                    description: "",
                    launch_mode: "UNKNOWN",
                }
            });
            nodeIds.add(source);
        }

        if (target && !nodeIds.has(target)) {
            nodeElements.push({
                data: {
                    id: target,
                    label: target,
                    node_label: target,
                    order: 0,
                    help: "",
                    animation: "idle",
                    script: "",
                    ui_file: "",
                    description: "",
                    launch_mode: "UNKNOWN",
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
    const scriptEl = document.getElementById("node-script");
    const modeEl = document.getElementById("node-launch-mode");
    const uiFileEl = document.getElementById("node-ui-file");
    const animationEl = document.getElementById("node-animation");
    const descriptionEl = document.getElementById("node-description");

    if (!nameEl || !helpEl || !orderEl) {
        return;
    }

    nameEl.textContent = node.data("label") || node.data("id") || "";
    helpEl.textContent = node.data("help") || "(none)";
    orderEl.textContent = String(node.data("order") ?? "");

    if (scriptEl) {
        scriptEl.textContent = node.data("script") || "(none)";
    }
    if (modeEl) {
        modeEl.textContent = node.data("launch_mode") || "UNKNOWN";
    }
    if (uiFileEl) {
        uiFileEl.textContent = node.data("ui_file") || "(none)";
    }
    if (animationEl) {
        animationEl.textContent = node.data("animation") || "idle";
    }
    if (descriptionEl) {
        descriptionEl.textContent = node.data("description") || "(none)";
    }
}


loadGraph();