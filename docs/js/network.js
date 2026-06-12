import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

d3.json("data/network_data.json").then(data => {

    // Establishing the graph constants and SVG object
    const w = 800;
    const h = 600;
    const padding = 5;

    const svg = d3.select("#network-chart")
        .append("svg")
            .attr("viewBox", [0, 0, w, h]) // Adds a viewbox
            .attr("width", "100%")
            .attr("height", "100%");

    // Appending a chart title
    svg.append("text")
        .attr("x", w / 2)
        .attr("y", 30)
        .attr("text-anchor", "middle")
        .style("font-size", "20px")
        .style("font-weight", "bold")
        .style("fill", "#333")
        .text("Topic and Ticker Sentiment Network");

    // The color scale conveys sentiment
    const colorScale = d3.scaleSequential(d3.interpolateRdYlGn)
        .domain([-1, 1]);

    // The size scale conveys volume
    const sizeScale = d3.scaleSqrt()
        .domain(d3.extent(data.nodes, d => d.volume))
        .range([4, 30]);

    // The link width scale conveys value
    const linkWidthScale = d3.scaleLinear()
        .domain(d3.extent(data.links, d => d.value))
        .range([1, 8]);

    // Maps edge values and link distances
    const linkDistanceScale = d3.scaleLinear()
        .domain(d3.extent(data.links, d => d.value))
        .range([150, 30]); // Edge value and link distance are inversely related

    // Defining an adjacency set to fade non-neighbors
    const adjacencySet = new Set();
    data.links.forEach(link => {
        adjacencySet.add(`${link.source}-${link.target}`);
        adjacencySet.add(`${link.target}-${link.source}`);
    });
    
    // Establishes the simulation object
    const simulation = d3.forceSimulation(data.nodes)
        // Pulls nodes to their respective sides according to type
        .force("x", d3.forceX(d => d.type === "ticker" ? 250: 500).strength(0.1))
        // Keeps the layout centered vertically on the screen
        .force("y", d3.forceY(h / 2).strength(0.05))
        // Adding repulsion to prevent clutter
        .force("charge", d3.forceManyBody().strength(-200))
        // Implements link force such that stronger edge values are closer
        .force("link", d3.forceLink(data.links)
            .id(d => d.id)
            .distance(d => linkDistanceScale(d.value))
            .strength(0.1))
        // Prevents nodes from overlapping
        .force("collision", d3.forceCollide().radius(d => sizeScale(d.volume) + padding));

    const dragBehavior = d3.drag()
        .on("start", (event, d) => {
            // Wakes up the simulation
            if (!event.active) simulation.alphaTarget(0.3).restart();
            // Fixes the node's position to the current mouse position
            d.fx = d.x;
            d.fy = d.y;
        })
        .on("drag", (event, d) => {
            // Updates the fixed position as the mouse moves
            d.fx = event.x;
            d.fy = event.y;
        })
        .on("end", (event, d) => {
            // Resets the simulation
            if (!event.active) simulation.alphaTarget(0); // Lets the simulation cool down
            d.fx = null; // Releases the x coordinate
            d.fy = null; // Releases the y coordinate
        });

    // Structuring the visual elements
    // Link group
    const linkGroup = svg.append("g")
            .attr("class", "links")
        .selectAll("line")
        .data(data.links)
        .join("line")
            .attr("stroke", "#999")
            .attr("stroke-opacity", 0.6)
            .attr("stroke-width", d => linkWidthScale(d.value));

    // Node group
    const nodeGroup = svg.append("g")
            .attr("class", "nodes")
        .selectAll("circle")
        .data(data.nodes)
        .join("circle")
            .attr("r", d => sizeScale(d.volume))
            .attr("fill", d => colorScale(d.sentiment))
            .call(dragBehavior)
            .on("mouseover", (event, d) => {
                const hoveredId = d.id;
                const isTicker = d.type === "ticker";

                // Fades out of non-neighbor nodes
                nodeGroup.style("opacity", neighbor => {
                    // Keeps the hovered node full visible
                    if (neighbor.id === hoveredId) return 1;

                    // Checking the adjacency set for related node types
                    const isConnected = isTicker
                        ? adjacencySet.has(`${hoveredId}-${neighbor.id}`)
                        : adjacencySet.has(`${neighbor.id}-${hoveredId}`);
                    
                    // Fades the hovered node if not connected
                    return isConnected ? 1 : 0.15;
                });
                
                // Fades out non-neighboring links
                linkGroup.style("opacity", link => {
                    // Connected links have sources or targets with matching 
                    const isLinkConnected = link.source.id === hoveredId || link.target.id === hoveredId;
                    return isLinkConnected ? 0.6 : 0.05;
                });
            })
            .on("mouseout", (event, d) => {
                // Resetting all nodes to full visibility
                nodeGroup.style("opacity", 1);
                // Resetting all links to original visibility
                linkGroup.style("opacity", 0.6);
            });

    nodeGroup.append("title")
            .text(d => `ID: ${d.id}\nType: ${d.type}\nVolume: ${d.volume}\nSentiment: ${d.sentiment.toFixed(2)}`);

    // Adding labels and tooltips
    const labelGroup = svg.append("g")
            .attr("class", "labels")
        .selectAll("text")
        .data(data.nodes.filter(d => (d.type === "topic" && d.volume > 1000) || d.type === "ticker"))
        .join("text")
            .text(d => d.id)
            .attr("font-size", "12px")
            .attr("text-anchor", "middle");

    // Establishing the color legend 
    // Defining the container for color gradient
    const defs = svg.append("defs");

    // Creating the color gradient
    const linearGradient = defs.append("linearGradient")
        .attr("id", "sentiment-gradient")
        .attr("x1", "0%")
        .attr("y1", "0%")
        .attr("x2", "100%")
        .attr("y2", "0%");

    // Adding color distinctions
    const numStops = 10;
    d3.range(numStops).forEach(i => {
        const pct = i / (numStops - 1);
        // Remapping a 0-1 percentage to the -1 to 1 sentiment plane
        const sentimentValue = -1 + (pct * 2);

        linearGradient.append("stop")
            .attr("offset", `${pct * 100}%`)
            .attr("stop-color", colorScale(sentimentValue));
    });

    // Creating a group for the color legend
    const colorLegendGroup = svg.append("g")
        .attr("class", "color-legend")
        .attr("transform", "translate(580, 30)"); // Positions the legend in the top-right
    
    // Draws the legend and fills it with the color gradient
    colorLegendGroup.append("rect")
        .attr("width", 150)
        .attr("height", 15)
        .attr("fill", "url(#sentiment-gradient)");

    // Adding a Negative label
    colorLegendGroup.append("text")
        .attr("x", 0)
        .attr("y", 30)
        .attr("text-anchor", "start")
        .attr("font-size", "10px")
        .text("Negative (-1)");

    // Adding the Neutral label
    colorLegendGroup.append("text")
        .attr("x", 75)
        .attr("y", 30)
        .attr("text-anchor", "middle")
        .attr("font-size", "10px")
        .text("Neutral (0)");

    // Adding the Positive label
    colorLegendGroup.append("text")
        .attr("x", 150)
        .attr("y", 30)
        .attr("text-anchor", "end")
        .attr("font-size", "10px")
        .text("Positive (1)");

    // Defining volume values for the size legend
    const sizeData = [
        { value: 100, label: "Low Volume"},
        { value: 1000, label: "Mid Volume"},
        { value: 5000, label: "High Volume" }
    ];

    // Creating a group for the size legend
    const sizeLegendGroup = svg.append("g")
        .attr("class", "size-legend")
        .attr("transform", "translate(40, 30)"); // Positions the legend in the top-left
    
    // Binds the reference sizes and creates a sub-group for each sizeLegend item
    const sizeItem = sizeLegendGroup.selectAll(".size-item")
        .data(sizeData)
        .join("g")
            .attr("class", "size-item")
            .attr("transform", (d, i) => `translate(${i * 100}, 0)`);

    // Appending a circle to each size item group
    sizeItem.append("circle")
        .attr("r", d => sizeScale(d.value))
        .attr("fill", "#ccc")
        .attr("stroke", "#667")
        .attr("stroke-width", 1);

    // Appending a text label next to each legend circle
    sizeItem.append("text")
        .attr("x", d => sizeScale(d.value) + 10) // Moves the text to the right of the circle
        .attr("y", 4) // Centers the text vertically with the circle
        .attr("font-size", "10px")
        .text(d => d.label);

    simulation.on("tick", () => {
        linkGroup
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);

        nodeGroup
            .attr("cx", d => d.x)
            .attr("cy", d => d.y);

        labelGroup
            .attr("x", d => d.x)
            .attr("y", d => d.y + 4);
        });
    }).catch(error => {
    console.error("Error loading the network data: ", error);
});