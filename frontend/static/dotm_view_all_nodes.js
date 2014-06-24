function addNodeToColaNodeList(nodeList, nodeIndex, node) {
	var n = {};
	n['name'] = node;
	n['width'] = 60;
	n['height'] = 40;
	nodeList.push(n);
	nodeIndex[node] = Object.keys(nodeIndex).length;
}

function loadNodesGraph(nodes, connections) {
	var width = 800,
	    height = 600,
	    r = 9;

	var color = d3.scale.category20();

	var d3cola = cola.d3adaptor()
	    .linkDistance(150)
	    .avoidOverlaps(true)
	    .size([width, height]);
	    //.jaccardLinkLengths(150);
	
	$("#stage").html("");
	var svg = d3.select("#stage").append("svg")
	    .attr("width", width)
	    .attr("height", height);
	
	d3.json('notused', function(error, graph) {
	/* FIXME: Don't want another JSON request here
	   especially because the backend should be 
	   agnostic to the specific renderer, therefore
	   fill in 'graph' JSON data here by convertion 
	   data passed via loadNodesGraph() parameters.
	*/

	// Map data 
	var i = 0;
	var nodeIndex = {};

	graph = new Array();
	graph["nodes"] = new Array();
	graph["links"] = new Array();
	graph["groups"] = new Array();
	$.each(nodes, function(index, data) {
		addNodeToColaNodeList(graph['nodes'], nodeIndex, data);
	});
	$.each(connections, function(index, data) {
		// Node sources and target might not exist
		// in case of non-managed nodes we connect to/from
		if(nodeIndex[data.source] == undefined)
			addNodeToColaNodeList(graph['nodes'], nodeIndex, data.source);
		if(nodeIndex[data.destination] == undefined)
			addNodeToColaNodeList(graph['nodes'], nodeIndex, data.destination);
		var l = {};
		l['source'] = nodeIndex[data.source];
		l['target'] = nodeIndex[data.destination];
		graph['links'].push(l);
	});

	// Do normal d3+cola rendering
	d3cola
	      .nodes(graph.nodes)
	      .links(graph.links)
	      .groups(graph.groups)
	      .start(5,15,20);
	
	var group = svg.selectAll(".group")
	      .data(graph.groups)
	      .enter().append("rect")
	      .attr("rx", r).attr("ry", r)
	      .attr("class", "group")
	      .style("fill", function (d, i) { return color(i); });
	
	var link = svg.selectAll(".link")
	      .data(graph.links)
	      .enter().append("line")
	      .attr("class", "link")
	      .style("stroke-width", function(d) { return Math.sqrt(d.value); });
	
	var pad = 3;
	var node = svg.selectAll(".node")
	            .data(graph.nodes)
		    .enter().append("rect")
	            .attr("class", "node")
	            .attr("width", function (d) { return d.width - 2 * pad; })
	            .attr("height", function (d) { return d.height - 2 * pad; })
	            .attr("rx", r - 3).attr("ry", r - 3)
	            .style("fill", function (d) { return color(0); })//color(graph.groups.length); })
	            .on("click", function (d) {
	                if (d3.event.defaultPrevented) return; // click suppressed
			if($.inArray(d.name, nodes) != -1) loadNode(d.name); 
	            })
	            .call(d3cola.drag);
	
	var label = svg.selectAll(".label")
	            .data(graph.nodes)
		    .enter().append("text")
	            .attr("class", "label")
	            .text(function (d) { return d.name; })
	            .on("click", function (d) {
			if (d3.event.defaultPrevented) return; // click suppressed
			if($.inArray(d.name, nodes) != -1) loadNode(d.name);
	            })
	            .call(d3cola.drag);
	
	node.append("title")
	      .text(function(d) { return d.name; });
	
	d3cola.on("tick", function() {
	            link.attr("x1", function (d) { return d.source.x = Math.max(r, Math.min(width - r, d.source.x)); })
	                .attr("y1", function (d) { return d.source.y = Math.max(r, Math.min(height - r, d.source.y)); })
	                .attr("x2", function (d) { return d.target.x = Math.max(r, Math.min(width - r, d.target.x)); })
	                .attr("y2", function (d) { return d.target.y = Math.max(r, Math.min(height - r, d.target.y)); });
	
	            node.attr("x", function (d) { return d.x = Math.max(r, Math.min(width - r, d.x - d.width / 2 + pad)); })
	                .attr("y", function (d) { return d.y = Math.max(r, Math.min(height - r, d.y - d.height / 2 + pad)); });
	            
	            group.attr("x", function (d) { return d.bounds.x = Math.max(r, Math.min(width - r, d.bounds.x)); })
	                 .attr("y", function (d) { return d.bounds.y = Math.max(r, Math.min(height - r, d.bounds.y)); })
	                .attr("width", function (d) { return d.bounds.width(); })
	                .attr("height", function (d) { return d.bounds.height(); });
	
	            label.attr("x", function (d) { return d.x = Math.max(r, Math.min(width - r, d.x + 3*r)); })
	                 .attr("y", function (d) {
	                     var h = this.getBBox().height;
	                     			return d.y = Math.max(r, Math.min(height - r, d.y + 2*r + h/4));
	                 });
	  });
	});
}
