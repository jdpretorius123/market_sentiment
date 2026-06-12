import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

d3.json("data/streamgraph_data.json").then(data => {

// Defining the dimensions and margins of the streamgraph
const margin = {top: 40, right: 30, bottom: 30, left: 0};
const width = 800 - margin.left - margin.right;
const height = 500 - margin.top - margin.bottom;

// Total width and height calculations for the viewbox
const totalWidth = width + margin.left + margin.right
const totalHeight = height + margin.top + margin.bottom;

// Formatting the date data
const parseDate = d3.utcParse("%Y-%m-%d");
data.forEach(d => {
    d.date = parseDate(d.date)
});

// Setting up the stack generator for the pos, neg, and neu series
const stack = d3.stack()
    .keys(["pos", "neu", "neg"])
    .offset(d3.stackOffsetWiggle)
    .order(d3.stackOrderInsideOut);

// Generating the stacked series
const series = stack(data);

// Finding the lowest and highest values across all layers and data points
const yMin = d3.min(series, layer => d3.min(layer, d => d[0]));
const yMax = d3.max(series, layer => d3.max(layer, d => d[1]));

// Creating an outer layer for the SVG object
const svgOuter = d3.select("#streamgraph")
    .append("svg")
        .attr("viewBox", [0, 0, totalWidth, totalHeight])
        .attr("width", "100%")
        .attr("height", "100%");

// Adding a main chart title
svgOuter.append("text")
    .attr("x", totalWidth / 2)
    .attr("y", 20)
    .attr("text-anchor", "middle")
    .style("font-size", "18px")
    .style("font-weight", "bold")
    .style("fill", "#333")
    .text("Sentiment Analysis Over Time");

// Appending the inner layer to the SVG object 
const svg = svgOuter.append("g")
        .attr("transform", `translate(${margin.left}, ${margin.top})`);

// Defining the x-axis scale
const x = d3.scaleUtc()
    .domain(d3.extent(data, d => d.date))
    .range([0, width]);

// Defining the y-axis scale
const y = d3.scaleLinear()
    .domain([yMin, yMax])
    .range([height, 0]);

// Mapping colors to each series
const color = d3.scaleOrdinal()
    .domain(["pos", "neu", "neg"])
    .range(["#2ca02c", "#7f7f7f", "#d62728"]);

// Applying the smoothing function to make the graph appealing
const area = d3.area()
    .curve(d3.curveBasis)
    .x(d => x(d.data.date))
    .y0(d => y(d[0]))
    .y1(d => y(d[1]));

// Binding each series to a SVG path element
svg.selectAll(".layer")
    .data(series)
    .join("path")
        .attr("class", "layer")
        .attr("fill", d => color(d.key))
        .attr("d", area);

// Adding an x-axis for the UTC dates to the SVG object
svg.append("g")
    .attr("transform", `translate(0, ${height})`)
    .call(d3.axisBottom(x));

// Binding each color to each series
const categories = ["pos", "neu", "neg"];

// Creating a display map
const labelMap = {
    pos: "Positive",
    neu: "Neutral",
    neg: "Negative"
};

const legendItems = d3.select("#streamgraph-legend")
    .selectAll(".legend-item")
    .data(categories)
    .join("div")
      .attr("class", "legend-item")
      .style("display", "flex")
      .style("align-items", "center")
      .style("margin-bottom", "4px");

legendItems.append("span")
    .style("width", "12px")
    .style("height", "12px")
    .style("margin-right", "6px")
    .style("background-color", d => color(d));

legendItems.append("span")
    .text(d => labelMap[d])
    .style("font-size", "12px");
}).catch(error => {
    console.error("Error loading the data: ", error);
})