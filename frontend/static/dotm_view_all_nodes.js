/* DOTM view displaying all node connections and faulty services */

function DOTMViewAllNodes(stage) {
	this.stage = stage;
	this.selectedNode = null;
	this.reload();
}

DOTMViewAllNodes.prototype.addNodeToColaNodeList = function(nodeList, nodeIndex, node, monitoring) {
	var n = {};
	n['name'] = node;
	n['width'] = 100;
	n['height'] = 40;

	if(monitoring[node]) {
		n['status'] = monitoring[node]['status'];
		/* add space for services */
		if(monitoring[node]['services_alerts']) {
			n['height'] += 30 * Object.keys(monitoring[node]['services_alerts']).length;
			n['services'] = monitoring[node]['services_alerts'];
		}
	} else {
		n['status'] = '';
	}

	nodeList.push(n);
	nodeIndex[node] = Object.keys(nodeIndex).length;
};

DOTMViewAllNodes.prototype.setData = function(data) {
	var view = this;
	var width = $(this.stage).width(),
	    height = $(this.stage).height(),
	    r = 9, margin = 0;

	var color = d3.scale.category20();

	var d3cola = cola.d3adaptor()
	    .linkDistance(150)
	    .avoidOverlaps(true)
	    .size([width, height]);
	    //.jaccardLinkLengths(150);
	
	$(this.stage).html("<form id='node_add' action='backend/nodes' method='POST'><input size='10' type='text' name='name'/><input type='submit' value='Add Node'/></form>");
	var svg = d3.select(this.stage).append("svg")
	    .attr("width", width)
	    .attr("height", height);
	
	// Map data 
	var i = 0;
	var nodeIndex = {};

	graph = new Array();
	graph["nodes"] = new Array();
	graph["links"] = new Array();
	graph["groups"] = new Array();
	$.each(data.nodes, function(index, nodeData) {
		view.addNodeToColaNodeList(graph['nodes'], nodeIndex, nodeData, data.monitoring);
	});
	$.each(data.connections, function(index, connectionData) {
		// Node sources and target might not exist
		// in case of non-managed nodes we connect to/from
		if(nodeIndex[connectionData.source] == undefined)
			view.addNodeToColaNodeList(graph['nodes'], nodeIndex, connectionData.source, data.monitoring);
		if(nodeIndex[connectionData.destination] == undefined)
			view.addNodeToColaNodeList(graph['nodes'], nodeIndex, connectionData.destination, data.monitoring);
		var l = {};
		l['source'] = nodeIndex[connectionData.source];
		l['target'] = nodeIndex[connectionData.destination];
		graph['links'].push(l);
	});

	// Do normal d3+cola rendering
	d3cola
	      .nodes(graph.nodes)
	      .links(graph.links)
	      .groups(graph.groups)
	      .start(5,15,20);

	svg.append('svg:defs').append('svg:marker').attr('id', 'end-arrow').attr('viewBox', '0 -5 10 10').attr('refX', 5).attr('markerWidth', 9).attr('markerHeight', 3).attr('orient', 'auto').append('svg:path').attr('d', 'M0,-5L10,0L0,5L2,0').attr('stroke-width', '0xp').attr('fill', '#555');
	
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
		.data(graph.nodes);

	node.enter().append("g")
		.attr("class", "node")
		.each(function(d) {
			d3.select(this)
			    .append("rect")
			    .attr("x", function (d) { return -d.width/2; })
			    .attr("y", function (d) { return -d.height/2; })
			    .attr("width", function (d) { return d.width - 2 * pad; })
			    .attr("height", function (d) { return d.height - 2 * pad; })
			    .attr("rx", r - 3).attr("ry", r - 3)
			    .attr("class", function (d) { return "node_rect node_" + d.name.replace('.',''); })
			    .style("fill", function (d) {
				if(d.status == 'UP')
					return '#0c3';
				if(d.status == 'DOWN')
					return '#f30';
				if(d.status == 'UNKNOWN')
					return '#fca';
				return 'white';
			    })
			    .style("stroke-width", 1)
			    .style("stroke", "gray")
			    .on("mouseover", function(d) {
				d3.select(this).style({'stroke-width':2,'stroke':'black'});
			    })
			    .on("mouseout", function(d) {
				if(d.name != view.selectedNode)
					d3.select(this).style({'stroke-width':1,'stroke':'gray'});
			    })
			    .on("click", function (d) {
				if (d3.event.defaultPrevented) return; // click suppressed
				if($.inArray(d.name, data.nodes) != -1) {
					d3.selectAll(".node_rect").style({'stroke-width':1,'stroke':'gray'});
					d3.select(this).style({'stroke-width':2,'stroke':'black'});
					view.selectedNode = d.name;
					loadNode(d.name);
				}
			    });

			if(d['services']) {
				var tmp = this;
				var pos = 0;
				$.each(d['services'], function(name, state) {
					d3.select(tmp)
					    .append("rect")
					    .attr("x", function(d) { return -d.width/2 + 2 * pad; })
					    .attr("y", function(d) { return pad + 18 + 12 + pos * 30 - d.height/2 })
					    .attr("height", function(d) { return 26; })
					    .attr("width", function(d) { return d.width - 6 - 4 * pad })
					    .attr("fill", function(d) {
						if(state == "CRITICAL")
							return "#F30";
						else 
							return "#FF0";
					    });

					d3.select(tmp)
					    .append("text")
					    .attr("dy", function(d) { return pad + 18 + 30 + pos * 30 - d.height/2 })
					    .attr("text-anchor", "middle")
					    .attr("class", "label")
					    .text(function (d) { return name; })

					pos++;
				});
			}

			d3.select(this)
			    .append("text")
			    .attr("dy", function(d) { return pad + 18 - d.height/2 })
			    .attr("class", "label")
			    .text(function (d) { return d.name; })
			    .on("mouseover", function(d) {
				d3.select(".node_"+d.name.replace('.','')).style({'stroke-width':2,'stroke':'black'});
			    })
			    .on("mouseout", function(d) {
				if(d.name != view.selectedNode)
					d3.select(".node_"+d.name.replace('.','')).style({'stroke-width':1,'stroke':'gray'});
			    })
			    .on("click", function (d) {
				if (d3.event.defaultPrevented) return; // click suppressed
				if($.inArray(d.name, data.nodes) != -1) {
					d3.selectAll(".node_rect").style({'stroke-width':1,'stroke':'gray'});
					d3.select(".node_"+d.name.replace('.','')).style({'stroke-width':2,'stroke':'black'});
					view.selectedNode = d.name;
					loadNode(d.name);
				}
			    });
		})
	        .call(d3cola.drag);

	d3cola.on("tick", function() {
		node.each(function (d) {
			return d.innerBounds = d.bounds.inflate(-margin);
		});
		link.each(function (d) {
			cola.vpsc.makeEdgeBetween(d, d.source.innerBounds, d.target.innerBounds, 5);
		});
		link.attr("x1", function (d) {
			return d.sourceIntersection.x;
		}).attr("y1", function (d) {
			return d.sourceIntersection.y;
		}).attr("x2", function (d) {
			return d.arrowStart.x;
		}).attr("y2", function (d) {
			return d.arrowStart.y;
		});

		node.attr("x", function (d) {
			return d.innerBounds.x;
		}).attr("y", function (d) {
			return d.innerBounds.y;
		}).attr("width", function (d) {
			return d.innerBounds.width();
		}).attr("height", function (d) {
			return d.innerBounds.height();
		});
	
/*	            group.attr("x", function (d) { return d.bounds.x = Math.max(r, Math.min(width - r, d.bounds.x)); })
	                 .attr("y", function (d) { return d.bounds.y = Math.max(r, Math.min(height - r, d.bounds.y)); })
	                .attr("width", function (d) { return d.bounds.width(); })
	                .attr("height", function (d) { return d.bounds.height(); });*/

		node.attr("transform", function (d) { return "translate(" + d.x + "," + d.y + ")"; });
	  });
};

DOTMViewAllNodes.prototype.reload = function() {
	var view = this;

	setStatus(this.stage, 'Fetching nodes...');
	$.getJSON("backend/nodes", {})
	.done(function (data) {
		clearStatus(view.stage);
		view.setData(data);
	})
	.fail(function (jqxhr, textStatus, error) {
		setError(view.stage, 'Node list fetch failed! ('+error+')');
	});

	// FIXME: hard-coded timeout
	setTimeout(view.reload, 30000);
};
