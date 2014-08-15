/* DOTM view displaying alert, service and connection detail tables for 
   a single node */

function DOTMViewNode(stage, node) {
	this.stage = stage;
	this.selectedNode = node;
	this.reload();
}

DOTMViewNode.prototype.setData = function(data) {
	var now = (new Date).getTime() / 1000;

	// Check fetch status
	try {
		if(data.status.fetch_status != "OK") {
			setError(this.stage, "Presented values are out-of-date! ("+data.status.fetch_status+")");
		} else {
			clearStatus(this.stage);
		}

		$(this.stage).html("\
			<div class='nodeChart'></div>\
			<div id='nodeTables'>\
				<div class='block'>\
					<div class='blockTitle'>Alerts</div>\
					<table class='alerts'></table>\
				</div>\
				<div class='block'>\
					<div class='blockTitle'>Services</div>\
					<table class='services'></table>\
				</div>\
				<div class='block'>\
					<div class='blockTitle'>Connections</div>\
					<table class='connections'></table>\
				</div>\
			</div>");

		// 1.) Setup tables

		// Fill in services
		var services = [];
		services.push('<tr><th>Process</th><th>Port</th><th>Last Up</th><th>Last Used</th></tr>');
		$.each(data.services, function(port, s) {
			var lastConn = "<td>never</td>";
			if(!isNaN(s.last_connection)) {
				lastConn = "<td class='timeago' title='"+s.last_connection*1000+"'>"+s.last_connection*1000+"</td>";
			}
			services.push('<tr class="service '+s.age+'"><td>'+s.process+'</td><td>'+port+'</td><td class="timeago" title="'+s.last_seen*1000+'">'+s.last_seen*1000+'</td>'+lastConn+'</tr>');
		})
		if(services.length > 1)
			$(".services").html(services.join(''));
		else
			$(".services").html("No services found!");

		// Fill in connections
		var connections = [];
		connections.push('<tr><th>I/O</th><th>Process</th><th>Port</th><th>Remote</th><th>Count</th><th>Seen</th></tr>');
		$.each(data.connections, function(service, c) {
			connections.push('<tr class="connection '+c.age+'"><td>'+c.direction+'</td><td>'+c.process+'</td><td>'+c.local_port+'</td><td>'+nodeLink(c.remote_host)+'</td><td>'+c.connections+'</td><td class="timeago" title="'+c.last_seen*1000+'">'+c.last_seen*1000+'</td></tr>');
		})
		if(connections.length > 1)
			$(".connections").html(connections.join(''));
		else
			$(".connections").html("No connections.");

		// Fill in alerts
		var alerts = [];
		alerts.push('<tr><th>Check Name</th><th>Service</th><th>Status</th><th>Last Check</th><th>Duration</th><th>Status Information</th></tr>');
		$.each(data.monitoring.services, function(index, s) {
			alerts.push('<tr class="alert status_'+s.status+'"><td class="service">'+s.service+'</td><td class="mapping">'+(s.mapping?s.mapping:'')+'</td><td class="alert_status">'+s.status+'</td><td class="last_check timeago" title="'+s.last_check*1000+'">'+s.last_check*1000+'</td><td class="last_status_change timeago" title="'+s.last_status_change*1000+'">'+s.last_status_change*1000+'</td><td class="status_information">'+s.status_information+'</td></tr>');
		});
		if(alerts.length > 1)
			$(".alerts").html(alerts.join(''));
		else
			$(".alerts").html("No monitoring data.");

		// Apply relative times
		$(".timeago").timeago();

		// 2.) Setup node chart

		var arrow;
		var tmp;
		var nodeDetails = "<table><tr><th></th><th></th><th>"+this.selectedNode+"</th><th></th><th></th></tr>";
		$.each(data.services, function(service, serviceData) {
			tmp = "";
			nodeDetails += "<tr class='service "+serviceData.age+"'><td>";
			$.each(data.connections, function(connection, connectionData) {
				if(connectionData.local_port == service &&
				   connectionData.direction == "in" &&
				   tmp.indexOf(">"+connectionData.remote_host+"<") == -1) {
					tmp += "<div class='node "+connectionData.age+"'>"+nodeLink(connectionData.remote_host)+"</div>";
					if(connectionData['remote_service']) {
						if(connectionData.remote_service['process']) {
							tmp += "<div class='remoteService service status_"+connectionData.remote_service.alert_status+"'>"+connectionData.remote_service.process+"</div>";
						}
					}
				}
			})
			nodeDetails += tmp + "<td>";
			if(tmp)
				nodeDetails += "<img src='arrow-right"+((serviceData.age=="fresh")?'':'-dashed')+".svg'/>";

			tmp = "";
			$.each(data.connections, function(connection, connectionData) {
				if(connectionData.process == serviceData.process &&
				   connectionData.direction == "out" &&
				   tmp.indexOf(">"+connectionData.remote_host+"<") == -1) {
					tmp += "<div class='node "+connectionData.age+"'>"+nodeLink(connectionData.remote_host);
					if(connectionData['remote_service']) {
						if(connectionData.remote_service['process']) {
							tmp += "<div class='remoteService service status_"+connectionData.remote_service.alert_status+"'>"+connectionData.remote_service.process+"</div>";
						}
					}
					tmp += "</div>";
				}
			})
			nodeDetails += "</td></td><td class='service status_"+(serviceData.alert_status?serviceData.alert_status:'')+"'>"+serviceData.process+"</td><td>";
			if(tmp)
				nodeDetails += "<img src='arrow-right"+((serviceData.age=="fresh")?'':'-dashed')+".svg'/>";
			nodeDetails += "</td><td>" + tmp + "</td></tr>";
		})
		nodeDetails += "</table>";
		$(".nodeChart").html(nodeDetails);
		$("#nodeTables").show();

		// Finally if there we no other exceptions check for monitoring
		// and complain if it is not there
		if(data.monitoring.node == null) {
			if(data.status['fetch_status'] != 'OK')
				throw("Monitoring fetch error: '"+data.status.fetch_status+"' Ensure that the dotm_node agent is installed and reachable!");
			else
				throw("No monitoring found! Ensure that your Nagios setup monitors this host with name '"+this.selectedNode+"' or add a <a href='javascript:setView(\"left\", new DOTMViewConfig(\".ui-layout-center .ui-layout-content\", \"user_node_aliases\"))'>node mapping</a>!");
		}
	} catch(err) {
		setError(this.stage, err);
	}

}

DOTMViewNode.prototype.reload = function() {
	var view = this;

	setStatus(this.stage, 'Fetching details for '+this.selectedNode+'...');

	$.getJSON("backend/nodes/"+this.selectedNode, {})
	.done(function (data) {
		clearStatus(view.stage);
		view.setData(data);
	})
	.fail(function (jqxhr, textStatus, error) {
		setError(view.stage, 'Node fetch failed! ('+error+')');
	})
};
