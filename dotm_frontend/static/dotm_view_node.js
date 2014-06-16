function loadNode(node) {
	// Clean everything
	setStatus('Fetching details for '+node+'...');
	$(".nodeChart").html("");
	$("#nodeTables").hide();

	$.getJSON("backend/nodes/"+node, {})
	.done(function (data) {
		var now = (new Date).getTime();

		// Check fetch status
		try {
			if(data.status.fetch_status != "OK") {
				throw "Node status is not 'OK' ("+data.status.fetch_status+")";
			}	

			// 1.) Setup tables

			// Fill in services
			var services = [];
			services.push('<tr><th>Process</th><th>Port</th><th>Last Up</th><th>Last Used</th></tr>');
			$.each(data.services, function(port, data) {
				var recent = "";
				var lastConn = "<td>never</td>";
				if(!isNaN(data.last_connection)) {
					lastConn = "<td class='timeago' title='"+data.last_connection*1000+"'>"+data.last_connection*1000+"</td>";
				} else {
					recent = "old";
				}
				if(now/1000 - data.last_seen > 6*60) {
					recent = "old";
				}
				services.push('<tr class="service '+recent+'"><td>'+data.process+'</td><td>'+port+'</td><td class="timeago" title="'+data.last_seen*1000+'">'+data.last_seen*1000+'</td>'+lastConn+'</tr>');
			})
			if(services.length > 1)
				$(".services").html(services.join(''));
			else
				$(".services").html("No services found!");

			// Fill in connections
			var connections = [];
			connections.push('<tr><th>I/O</th><th>Process</th><th>Port</th><th>Remote</th><th>Count</th><th>Seen</th></tr>');
			$.each(data.connections, function(service, data) {
				var recent = "";
				if(now/1000 - data.last_seen > 6*60) {
					recent = "old";
				}
				connections.push('<tr class="connection '+recent+'"><td>'+data.direction+'</td><td>'+data.process+'</td><td>'+data.localPort+'</td><td>'+nodeLink(data.remoteHost)+'</td><td>'+data.connections+'</td><td class="timeago" title="'+data.last_seen*1000+'">'+data.last_seen*1000+'</td></tr>');
			})
			if(connections.length > 0)
				$(".connections").html(connections.join(''));
			else
				$(".connections").html("No connections.");

			setStatus(node+' successfully loaded.');

			// Apply relative times
			$(".timeago").timeago();

			// 2.) Setup node chart

			var arrow;
			var tmp;
			var nodeDetails = "<table><tr><th></th><th></th><th>"+node+"</th><th></th><th></th></tr>";
			$.each(data.services, function(service, serviceData) {
				tmp = "";
				nodeDetails += "<tr class='service'><td>";
				$.each(data.connections, function(connection, connectionData) {
					if(connectionData.localPort == service &&
					   connectionData.direction == "in" &&
					   tmp.indexOf(">"+connectionData.remoteHost+"<") == -1) {
						tmp += "<div class='node'>"+nodeLink(connectionData.remoteHost)+"</div>";
					}
				})
				nodeDetails += tmp + "<td>";
				if(tmp)
					nodeDetails += "<img src='arrow-right.svg'/>";

				tmp = "";
				$.each(data.connections, function(connection, connectionData) {
					if(connectionData.process == serviceData.process &&
					   connectionData.direction == "out" &&
					   tmp.indexOf(">"+connectionData.remoteHost+"<") == -1) {
						tmp += "<div class='node'>"+nodeLink(connectionData.remoteHost)+"</div>";
					}
				})
				nodeDetails += "</td></td><td class='service'>"+serviceData.process+"</td><td>";
				if(tmp)
					nodeDetails += "<img src='arrow-right.svg'/>";
				nodeDetails += "</td><td>" + tmp + "</td></tr>";
			})
			nodeDetails += "</table>";
			$(".nodeChart").html(nodeDetails);
			$("#nodeTables").show();
		} catch(err) {
			setError(err);
		}
	})
	.fail(function (jqxhr, textStatus, error) {
		setError('Node fetch failed! ('+error+')');
	})
}
