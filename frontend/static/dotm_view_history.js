/* Simple view that generates HTML forms and fills values from JSON */

function DOTMViewHistory(stage) {
	this.stage = stage;
}

DOTMViewHistory.prototype.reload = function() {
	var view = this;

	// Clean everything
	setStatus(this.stage, 'Fetching snapshot list...');
	$(this.stage).html("");

	$.getJSON("backend/history", {})
	.done(function (data) {
		var navigation, list;
		var selected = getHistoryIndex();
		var selectedIndex = -1;
		
		list = "<h3>List of Snapshots</h3><div class='history'>";
		$.each(data, function(index, timestamp) {
			list += "<div class='snapshot'><a href='javascript:setHistoryIndex(\""+timestamp+"\")'>"+timestamp+"</a><div>";
			if(selected != "" && selected == timestamp)
				selectedIndex = index;
		});
		list += "</div></div>";

		if(selected != "" && selectedIndex == -1)
			setError(view.stage, "Invalid snapshot selection. Snapshot '"+selected+"' doesn't exist!");

		// Append navigation after we know about index of previous and next snapshot
		navigation = "<div class='settingsForm'>";

		if(selected != "")
			navigation +=
				"<p>Currently selected snapshot is '"+selected+"'</p>" +
				"<p>" +
				"<input type='button' value='Reset to Live View' onclick='setHistoryIndex(\"\")'/>" +
				"</p><p>" +
				"<input type='button' value='&lt;&lt;&lt;' title='Previous Snapshot' onclick='setHistoryIndex(\""+data[selectedIndex - 1]+"\")'/>"+
				"<input type='button' value='>>>' title='Next Snapshot' onclick='setHistoryIndex(\""+data[selectedIndex + 1]+"\")'/>"+
				"</p>";
		else
			navigation += "<p>Select a snapshot to view a past system state.</p>";

		$(view.stage).html(navigation + list);
		clearStatus(view.stage);
	})
	.fail(function (jqxhr, textStatus, error) {
		setError(view.stage, 'Fetching snapshot list failed! ('+error+')');
	})
}
