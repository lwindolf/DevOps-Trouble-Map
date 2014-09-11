/* DOTM view displaying all node connections and faulty services */

function DOTMViewAllNodes(stage) {
	this.stage = stage;		/* parent <div> selector */
	this.selectedNode = null;
	this.graph = null;
	this.viewBoxX = 0;		/* panning coordinates */
	this.viewBoxY = 0;
	this.nodePositions = new Array();
	this.reload();
}

DOTMViewAllNodes.prototype.addNodeToColaNodeList = function(nodeList, nodeIndex, node, monitoring) {
	var n = {};
	n['name'] = node;
	n['width'] = 100;
	n['height'] = 40;

	/* We expect a node label font size of 10pt! */
	n['width'] = 6 * n['name'].length + 48;

	if(monitoring[node]) {
		n['status'] = monitoring[node]['status'];

		/* add space for services */
		if(monitoring[node]['services_alerts']) {
			n['height'] += 30 * Object.keys(monitoring[node]['services_alerts']).length;
			n['services'] = $.extend({}, monitoring[node]['services_alerts']);
		}
		if(monitoring[node]['other_alerts']) {
			n['height'] += 30 * Object.keys(monitoring[node]['other_alerts']).length;
			n['services'] = $.extend(n['services'], monitoring[node]['other_alerts']);
		}
	} else {
		n['status'] = '';
	}

	if(this.nodePositions[node]) {
		n.x = this.nodePositions[node].x;
		n.y = this.nodePositions[node].y;
	}

	nodeList.push(n);
	nodeIndex[node] = Object.keys(nodeIndex).length;
};

// FIXME: dirty workaround, sometimes auto-grouping causes group without
// leaves which causes an Exception, which we do not want
function fixGroups(g) {
	if (g.groups) {
		g.groups.forEach(function (cg) {
			return fixGroups(cg);
		});
	}
	if (g.leaves)
		return;

	g.leaves = new Array();
}

DOTMViewAllNodes.prototype.setData = function(data) {
	var view = this;
	var powerGraph;
	var width = $(this.stage).width(),
	    height = $(this.stage).height(),
	    r = 9, margin = 0;

	var color = d3.scale.category20();

	var d3cola = cola.d3adaptor()
	    .convergenceThreshold(0.01)
	    .linkDistance(150)
	    .avoidOverlaps(true)
	    .size([width, height]);
	
	$(this.stage).html("");
	$(this.stage).css("overflow", "hidden");
	var svg = d3.select(this.stage).append("svg")
	    .attr("width", width)
	    .attr("height", height);

	// Allow panning as suggested in by dersinces (CC BY-SA 3.0) in
	// http://stackoverflow.com/questions/20099299/implement-panning-while-keeping-nodes-draggable-in-d3-force-layout
	var drag = d3.behavior.drag();
	drag.on('drag', function() {
	    view.viewBoxX -= d3.event.dx;
	    view.viewBoxY -= d3.event.dy;
	    svg.select('g.node-area').attr('transform', 'translate(' + (-view.viewBoxX) + ',' + (-view.viewBoxY) + ')');
	});
	svg.append('rect')
	  .classed('bg', true)
	  .attr('stroke', 'transparent')
	  .attr('fill', 'transparent')
	  .attr('x', 0)
	  .attr('y', 0)
	  .attr('width', width)
	  .attr('height', height)
	  .call(drag);

	var nodeArea = svg.append('g').classed('node-area', true);

	// Restore previous panning
	svg.select('g.node-area').attr('transform', 'translate(' + (-view.viewBoxX) + ',' + (-view.viewBoxY) + ')');
	
	// Map data 
	var i = 0;
	var nodeIndex = {};

	view.graph = new Array();
	view.graph["nodes"] = new Array();
	view.graph["links"] = new Array();
	$.each(data.nodes, function(index, nodeData) {
		view.addNodeToColaNodeList(view.graph['nodes'], nodeIndex, nodeData, data.monitoring);
	});
	$.each(data.connections, function(index, connectionData) {
		// Node sources and target might not exist
		// in case of non-managed nodes we connect to/from
		if(nodeIndex[connectionData.source] == undefined)
			view.addNodeToColaNodeList(view.graph['nodes'], nodeIndex, connectionData.source, data.monitoring);
		if(nodeIndex[connectionData.destination] == undefined)
			view.addNodeToColaNodeList(view.graph['nodes'], nodeIndex, connectionData.destination, data.monitoring);
		var l = {};
		l['source'] = nodeIndex[connectionData.source];
		l['target'] = nodeIndex[connectionData.destination];
		view.graph['links'].push(l);
	});

	var doLayout = function () {

	svg.append('svg:defs').append('svg:marker').attr('id', 'end-arrow').attr('viewBox', '0 -5 10 10').attr('refX', 5).attr('markerWidth', 9).attr('markerHeight', 3).attr('orient', 'auto').append('svg:path').attr('d', 'M0,-5L10,0L0,5L2,0').attr('stroke-width', '0xp').attr('fill', '#555');

	var group = nodeArea.selectAll(".group")
	      .data(powerGraph.groups)
	      .enter().append("rect")
	      .attr("rx", r).attr("ry", r)
	      .attr("class", "group")
	      .style("fill", function (d, i) { return '#ddd8ae'; });
	
	var link = nodeArea.selectAll(".link")
	      .data(powerGraph.powerEdges)
	      .enter().append("line")
	      .attr("class", "link")
	      .style("stroke-width", function(d) { return Math.sqrt(d.value); });
	
	var pad = 3;
	var node = nodeArea.selectAll(".node")
		.data(view.graph.nodes);

	node.enter().append("g")
		.attr("class", "node")
		.each(function(d) {
			if(d.name == "Internet") {
				d3.select(this)
				    .append("svg:image")
				    .attr("xlink:href", "cloud.png")
				    .attr("width", "100px")
				    .attr("height", "40px")
				    .attr("preserveAspectRatio", "none")
				    .attr("x", "-50px")
				    .attr("y", "-20px");
			} else {
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
						return '#fff';
					if(d.status == 'DOWN')
						return '#f30';
					if(d.status == 'UNKNOWN')
						return '#fca';
					if($.inArray(d.name, data.nodes) == -1)
						return '#eee';

					return 'white';
				    })
				    .style("stroke-width", 1)
				    .style("stroke", "gray")
				    .on("mouseover", function(d) {
					if($.inArray(d.name, data.nodes) != -1)
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
			}

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
		})
	        .call(d3cola.drag);

	if(view.nodePositions.length == 0) {
		setStatus(this.stage, "Calculating layout...");
		d3cola.start(10,20,30);
	} else {
		/* Do only a few full constraint iterations */
		d3cola.start(0,0,5);
	}

	d3cola.on("tick", function() {
                node.each(function (d) {
                    d.bounds.setXCentre(d.x);
                    d.bounds.setYCentre(d.y);
                    d.innerBounds = d.bounds.inflate(-margin);
                });
                group.each(function (d) {
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
	
                group.attr("x", function (d) {
                    return d.innerBounds.x;
                }).attr("y", function (d) {
                    return d.innerBounds.y;
                }).attr("width", function (d) {
                    return d.innerBounds.width();
                }).attr("height", function (d) {
                    return d.innerBounds.height();
                });

		node.attr("transform", function (d) { return "translate(" + d.x + "," + d.y + ")"; });
	  });
	};

	d3cola.nodes(view.graph.nodes)
	      .links(view.graph.links)
	      .powerGraphGroups(function (d) {
		    return (powerGraph = d).groups.forEach(function (v) {
			return v.padding = 10;
		    });
	      });

	powerGraph.groups.forEach(function (g) { fixGroups(g); });
	doLayout();

	if(getHistoryIndex() != "")
		setWarning(view.stage, "Warning: you are viewing historic data! <input type='button' value='Reset to Live View' onclick='javascript:setHistoryIndex(\"\");'/>");
};

DOTMViewAllNodes.prototype.reload = function() {
	var view = this;

	/* save old node positions */
	if(view.graph) {
		view.graph.nodes.forEach(function (e) {
			if(!view.nodePositions[e.name])
				view.nodePositions[e.name] = new Array();
			view.nodePositions[e.name].x = e.x;
			view.nodePositions[e.name].y = e.y;
		});
	}

	setStatus(this.stage, 'Updating...');
	$.getJSON("backend/nodes"+getParams(), {})
	.done(function (data) {
		clearStatus(view.stage);
		view.setData(data);
	})
	.fail(function (jqxhr, textStatus, error) {
		setError(view.stage, 'Node list fetch failed! ('+error+')');
	});
};
