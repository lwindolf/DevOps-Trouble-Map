/* Simple view that generates a list of nodes and forms to manipulate it */

var manage_nodes_view;

function DOTMViewManageNodes(stage, anchor) {
	this.stage = stage;
	this.loadConfig(anchor);
	manage_nodes_view = this;	// FIXME: ugly
}

function addNode(node) {
	view = manage_nodes_view;

	setStatus(view.stage, 'Adding node "'+node+'"...');
	$.post("backend/nodes", { action: 'add', name: node })
	.done(function (data) {
		clearStatus(view.stage);
		view.loadConfig();
	})
	.fail(function (jqxhr, textStatus, error) {
		setError(view.stage, 'Node adding failed! ('+error+')');
	});
}

function removeNode(node) {
	view = manage_nodes_view;

	setStatus(view.stage, 'Removing node "'+node+'"...');
	$.post("backend/nodes", { action: 'remove', name: node })
	.done(function (data) {
		clearStatus(view.stage);
		view.loadConfig();
	})
	.fail(function (jqxhr, textStatus, error) {
		setError(view.stage, 'Node removal failed! ('+error+')');
	});
}

DOTMViewManageNodes.prototype.loadConfig = function(anchor) {
	var view = this;

	// Clean everything
	setStatus(this.stage, 'Fetching nodes...');
	$(this.stage).html("");

	// Fetch existing host list
	$.getJSON("backend/nodes", {})
	.done(function (data) {
		var html = "<div class='settingsForm'><h3>Known Nodes</h3><table border='0'>";

		/* Print forms for existing nodes */
		$.each(data.nodes.sort(), function(index, node) {
			html += "<tr><td>" + node + "</td><td>";
			html += "<a name='" + node + "'/>";
			html += "<input type='button' value='Remove' onclick='javascript:removeNode(\""+node+"\")'/>";
			html += "</td></tr>";
		});
		html += "</td></tr></table>";
		html += "<h3>Add Node</h3>";
		html += "<input id='add_node_name' type='text'/>";
		html += "<input type='button' value='Add' onclick='javascript:addNode($(\"#add_node_name\").val())'/>";
		html += "</form></div>";
		$(view.stage).append(html);

		if(anchor)
			location.hash = "#" + anchor;	/* scroll to form selected */
	})
	.fail(function (jqxhr, textStatus, error) {
		setError(view.stage, 'Fetching nodes failed! ('+error+')');
	})

	// Fetch host suggestions
	$.getJSON("backend/nodes/suggestions", {})
	.done(function (data) {
		var html = "<div class='settingsForm'><h3>Suggestions</h3><p>You might want to add the following nodes too. These suggesting are based on the host names by the NSS configuration.</p><table border='0'>";
		/* Print forms for existing nodes */
		$.each(data.nodes.sort(), function(index, node) {
			html += "<tr><td>" + node + "</td><td>";
			html += "<a name='" + node + "'/>";
			html += "<input type='button' value='Add' onclick='javascript:addNode(\""+node+"\")'/>";
			html += "</td></tr>";
		});
		html += "</td></tr></table>";
		html += "</div>";
		$(view.stage).append(html);

		clearStatus(view.stage);
	})
	.fail(function (jqxhr, textStatus, error) {
		setError(view.stage, 'Fetching suggestion failed! ('+error+')');
	})
}


DOTMViewManageNodes.prototype.reload = function() {
	// We don't reload for simplicity
};
