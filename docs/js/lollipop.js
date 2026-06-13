import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

  d3.json("data/lollipop_data.json").then(rawData => {

      // Deriving net sentiment (positive minus negative) per ticker
      const data = rawData
          .map(d => ({ ticker: d.ticker, net: d.net }))
          .sort((a, b) => d3.descending(a.net, b.net));

      // Mirroring the CSS sentiment tokens (JS can't read CSS custom props cheaply)
      const colorPos = "#2ca02c"; // --color-pos
      const colorNeg = "#d62728"; // --color-neg

      // Specifying the responsive viewBox dimensions and margins
      const svgWidth = 760;
      const svgHeight = 460;
      const margin = { top: 30, right: 70, bottom: 55, left: 70 };
      const innerWidth = svgWidth - margin.left - margin.right;
      const innerHeight = svgHeight - margin.top - margin.bottom;

      // Building an x-domain that anchors at zero and tolerates a future negative net
     const [dataMin, dataMax] = d3.extent(data, d => d.net);
     const xPad = (dataMax - dataMin) * 0.1 || 0.01;
     const xLow = dataMin - xPad;
     const xHigh = dataMax + xPad;

      // Establishing the scales
      const xScale = d3.scaleLinear()
          .domain([xLow, xHigh])
          .range([0, innerWidth]);

      const yScale = d3.scaleBand()
          .domain(data.map(d => d.ticker))
          .range([0, innerHeight])
          .padding(0.4);

      // Initializing the SVG object
      const selector = "#lollipop-chart";
      d3.select(selector).selectAll("*").remove();

      const svg = d3.select(selector)
          .append("svg")
          .attr("width", svgWidth)
          .attr("height", svgHeight)
          .attr("viewBox", `0 0 ${svgWidth} ${svgHeight}`)
          .style("background-color", "white")
          .style("box-shadow", "0 4px 8px rgba(0, 0, 0, 0.1)");

      // Translating into the plotting area inside the margins
      const plot = svg.append("g")
          .attr("transform", `translate(${margin.left}, ${margin.top})`);

      // Drawing light vertical gridlines behind the marks
      plot.append("g")
          .attr("class", "gridlines")
          .selectAll("line")
          .data(xScale.ticks(5))
          .enter()
          .append("line")
          .attr("x1", d => xScale(d))
          .attr("x2", d => xScale(d))
          .attr("y1", 0)
          .attr("y2", innerHeight)
          .style("stroke", "#eee")
          .style("stroke-width", "1px");

      // Drawing the x-axis
      plot.append("g")
          .attr("class", "x-axis")
          .attr("transform", `translate(0, ${innerHeight})`)
          .call(d3.axisBottom(xScale).ticks(5).tickFormat(d3.format("+.2f")))
          .selectAll("text")
          .style("font-size", "11px")
          .style("fill", "#333");

      // Drawing the y-axis with ticker labels
      plot.append("g")
          .attr("class", "y-axis")
          .call(d3.axisLeft(yScale).tickSize(0))
          .call(g => g.select(".domain").remove())
          .selectAll("text")
          .style("font-size", "13px")
          .style("font-weight", "bold")
          .style("fill", "#333");

      // Binding one group per ticker
      const rows = plot.selectAll(".lollipop")
          .data(data)
          .enter()
          .append("g")
          .attr("class", "lollipop")
          .attr("transform", d => `translate(0, ${yScale(d.ticker) + yScale.bandwidth() / 2})`);

      // Drawing the stems, growing them out from x(0) on entrance
      rows.append("line")
          .attr("class", "stem")
          .attr("x1", xScale(xLow))
          .attr("x2", xScale(xLow))
          .attr("y1", 0)
          .attr("y2", 0)
          .style("stroke", d => d.net >= 0 ? colorPos : colorNeg)
          .style("stroke-width", "2px")
          .transition()
          .duration(1000)
          .attr("x2", d => xScale(d.net));

      // Drawing the dots, fading and sliding them to their final position
      rows.append("circle")
          .attr("class", "dot")
          .attr("cx", xScale(xLow))
          .attr("cy", 0)
          .attr("r", 6)
          .style("fill", d => d.net >= 0 ? colorPos : colorNeg)
          .style("opacity", 0)
          .transition()
          .duration(1000)
          .attr("cx", d => xScale(d.net))
          .style("opacity", 1);

      // Labeling each dot with its formatted net value
      rows.append("text")
          .attr("class", "value-label")
          .attr("x", xScale(xLow))
          .attr("y", 0)
          .attr("dy", "-0.8em")
          .attr("text-anchor", "middle")
          .text(d => d3.format("+.3f")(d.net))
          .style("font-size", "11px")
          .style("fill", "#333")
          .style("opacity", 0)
          .transition()
          .duration(1000)
          .attr("x", d => xScale(d.net))
          .style("opacity", 1);

      // Labeling the x-axis
      svg.append("text")
          .attr("class", "x-axis-label")
          .attr("x", margin.left + innerWidth / 2)
          .attr("y", svgHeight - 12)
          .attr("text-anchor", "middle")
          .text("Net sentiment (positive − negative)")
          .style("font-size", "12px")
          .style("font-weight", "bold")
          .style("fill", "#333");

  }).catch(error => {
      console.error("Error loading the lollipop data: ", error);
  });