import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

d3.json("data/radar_data.json").then(rawData => {

    // Ordering the data alphabetically
    const data = rawData.sort((a,b) => a.ticker.localeCompare(b.ticker));

    // Establishing the grid layout for the radar charts
    const cols = 2;
    const rows = 5;
    const cellWidth = 220;
    const cellHeight = 220;
    const cellRadius = 75;

    // Specifying the dimensions for the reference chart
    const refAreaHeight = 250;
    const svgWidth = cols * cellWidth;
    const svgHeight = refAreaHeight + (rows * cellHeight);

    // Specifying the axes for the reference chart
    const features = ["pos", "neu", "neg"];
    const featureLabels = { pos: "Positive", neu: "Neutral", neg: "Negative"};
    const angleSlice = (Math.PI * 2) / features.length;

    // Establishing the shared scales and generators
    const rScale = d3.scaleLinear()
        .domain([0, 1])
        .range([0, cellRadius]);

    const radarLine = d3.lineRadial()
        .angle((d, i) => i * angleSlice - Math.PI / 2)
        .radius(d => rScale(d.value))
        .curve(d3.curveLinearClosed);

    // Initializing the SVG object
    const selector = "#radar-chart";
    d3.select(selector).selectAll("*").remove();

    const svg = d3.select(selector)
        .append("svg")
        .attr("width", svgWidth)
        .attr("height", svgHeight)
        .attr("viewBox", `0 0 ${svgWidth} ${svgHeight}`)
        .style("background-color", "white")
        .style("box-shadow", "0 4px 8px rgba(0, 0, 0, 0.1)");

    // Drawing the reference chart
    const refGroup = svg.append("g")
        .attr("transform", `translate(${svgWidth / 2}, ${refAreaHeight / 2})`);
    
    drawRadar(refGroup, { ticker: "Scale Guide", pos: 0.3, neu: 0.5, neg: 0.2}, true);

    // Drawing the 5x2 grid
    const gridContainer = svg.append("g")
        .attr("transform", `translate(0, ${refAreaHeight})`);

    const cells = gridContainer.selectAll(".cell")
        .data(data)
        .enter()
        .append("g")
        .attr("class", "cell")
        .attr("transform", (d, i) => {
            const x = (i % cols) * cellWidth + (cellWidth / 2);
            const y = Math.floor(i / cols) * cellHeight + (cellHeight / 2);
            return `translate(${x}, ${y})`;
        });

    cells.each(function(d) {
        drawRadar(d3.select(this), d, false);
    });

    // Defining the core drawing function
    function drawRadar(container, d, isReference) {
        const gridLevels = [0.25, 0.5, 0.75, 1.0];

        // Declaring the grid rings
        container.selectAll(".grid-circle")
            .data(gridLevels)
            .enter()
            .append("circle")
            .attr("class", "grid-circle")
            .attr("r", level => rScale(level))
            .style("fill", "none")
            .style("stroke", "#ccc")
            .style("stroke-width", "1px")
            .style("stroke-dasharray", "2, 2");

        // Declaring the spokes
        container.selectAll(".axis-line")
            .data(features)
            .enter()
            .append("line")
            .attr("class", "axis-line")
            .attr("x1", 0)
            .attr("y1", 0)
            .attr("x2", (f, i) => rScale(1) * Math.cos(i * angleSlice - Math.PI / 2))
            .attr("y2", (f, i) => rScale(1) * Math.sin(i * angleSlice - Math.PI / 2))
            .style("stroke", "#999")
            .style("stroke-width", "1px");

        // Establishing the polygon
        const polygonData = features.map(f => ({ axis: f, value: d[f] }));

        container.append("path")
            .datum(polygonData)
            .attr("class", "radar-polygon")
            .attr("d", radarLine)
            .style("fill", "#4682b4")
            .style("fill-opacity", 0.4)
            .style("stroke", "#4682b4")
            .style("stroke-width", "1.5px")
            .attr("stroke-dasharray", function() { return this.getTotalLength() + " " + this.getTotalLength(); })
            .attr("stroke-dashoffset", function() { return this.getTotalLength(); })
            .transition()
            .duration(1000)
            .attr("stroke-dashoffset", 0);

        // Specifying the title
        container.append("text")
            .attr("class", "cell-title")
            .attr("y", cellRadius + 25)
            .text(d.ticker)
            .style("font-size", "14px")
            .style("font-weight", "bold")
            .style("fill", "#333")
            .style("text-anchor", "middle");

        // Declaring the labels for the reference chart
        if (isReference) {
            container.selectAll(".axis-label")
                .data(features)
                .enter()
                .append("text")
                .attr("class", "axis-label")
                .attr("x", (f, i) => rScale(1.2) * Math.cos(i * angleSlice - Math.PI / 2))
                .attr("y", (f, i) => rScale(1.2) * Math.sin(i * angleSlice - Math.PI / 2))
                .attr("text-anchor", "middle")
                .attr("alignment-baseline", "middle")
                .text(f => featureLabels[f])
                .style("font-size", "12px")
                .style("fill", "#333")
                .style("font-weight", "bold");
            }
        }
    }).catch(error => {
        console.error("Error loading the radar data: ", error);
});
