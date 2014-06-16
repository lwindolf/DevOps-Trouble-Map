/* Simle view that generates HTML forms and fills values from JSON */

function printConfigForm(title, setting, type, addAllowed, keyTitle, valueTitle) {
	var result = "<div class='settingsForm'>";
	result += "<div class='title'>"+title+"</div>";
	result += "<div class='description'>"+setting.description+"</div>";
	result += "<form action='FIXME' method='POST'>";
	if(type == 'single_value') {
		result += "<input type='text' value='"+setting.values+"'/>";
		result += "<input type='submit' value='Save'/>";
	}
	if(type == 'hash') {
		result += "<table>";
		result += "<tr><th>"+keyTitle+"</th><th>"+valueTitle+"</th></tr>";
		$.each(setting.values, function(key, value) {
			result += "<tr><td>";
			result += "<input type='text' name='key' value='"+key+"' readonly/>";
			result += "</td><td>";
			result += "<input type='text' name='value' value='"+value+"'/>";
			result += "<input type='button' value='Remove'/>";
			result += "</td></tr>";
		});
		result += "</table>";
		if(addAllowed) {
			result += "<table>";
			result += "<tr><th>"+keyTitle+"</th><th>"+valueTitle+"</th></tr>";
			result += "<tr><td>";
			result += "<input type='text' name='key' value=''/>";
			result += "</td><td>";
			result += "<input type='text' name='value' value=''/>";
			result += "<input type='button' value='Add'/>";
			result += "</td></tr>";
			result += "</table>";
		}
	}
	result += "</form>";
	result += "</div>";
	return result;
}

function loadConfig() {
	// Clean everything
	setStatus('Fetching settings...');
	// FIXME: Use a stage div instead of nodeChart!
	$(".nodeChart").html("");
	$("#nodeTables").hide();

	$.getJSON("backend/settings", {})
	.done(function (data) {
		var forms = "";

		forms += printConfigForm('Internal Networks', data.other_internal_networks, 'single_value', false);
		forms += printConfigForm('Node Aliases', data.user_node_aliases, 'hash', true, 'Alias', 'Node Name');
		$(".nodeChart").html(forms);

		setStatus("Settings loaded.");
	})
	.fail(function (jqxhr, textStatus, error) {
		setError('Fetching settings failed! ('+error+')');
	})
}
