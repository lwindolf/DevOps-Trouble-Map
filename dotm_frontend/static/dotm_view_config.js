/* Simle view that generates HTML forms and fills values from JSON */

function printConfigForm(title, setting, addAllowed, keyTitle, valueTitle) {
	var result = "<div class='settingsForm'>";
	result += "<div class='title'>"+title+"</div>";
	result += "<div class='description'>"+setting.description+"</div>";
	result += "<form action='FIXME' method='POST'>";
	if(setting.type == 'single_value') {
		result += "<input type='text' value='"+(setting.values?setting.values:"")+"'/>";
		result += "<input type='submit' value='Save'/>";
	}
	if(setting.type == 'array') {
		result += "<table>";
		result += "<tr><th>"+keyTitle+"</th></tr>";
		$.each(setting.values, function(index, value) {
			result += "<tr><td>";
			result += "<input type='text' name='key' value='"+value+"' readonly/>";
			result += "<input type='button' value='Remove'/>";
			result += "</td></tr>";
		});
		result += "</table>";
		if(addAllowed) {
			result += "<table>";
			result += "<tr><th>"+keyTitle+"</th></tr>";
			result += "<tr><td>";
			result += "<input type='text' name='key' value=''/>";
			result += "<input type='button' value='Add'/>";
			result += "</td></tr>";
			result += "</table>";
		}
	}
	if(setting.type == 'hash') {
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

		forms += printConfigForm('Internal Networks', data.other_internal_networks, true, 'Network');
		forms += printConfigForm('Use Nagios Aliases', data.nagios_use_aliases);
		forms += printConfigForm('Node Aliases', data.user_node_aliases, true, 'Alias', 'Node Name');
		forms += printConfigForm('Service Aging', data.service_aging);
		forms += printConfigForm('Connection Aging', data.connection_aging);
		forms += printConfigForm('Service Data Retention', data.service_expire);
		forms += printConfigForm('Connection Data Retention', data.connection_expire);
		forms += printConfigForm('Old Service Hiding', data.service_hiding);
		forms += printConfigForm('Old Connection Hiding', data.connection_hiding);

		$(".nodeChart").html(forms);

		setStatus("Settings loaded.");
	})
	.fail(function (jqxhr, textStatus, error) {
		setError('Fetching settings failed! ('+error+')');
	})
}
