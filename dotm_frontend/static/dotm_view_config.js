/* Simle view that generates HTML forms and fills values from JSON */
function loadConfig() {
	// Clean everything
	setStatus('Fetching settings...');
	// FIXME: Use a stage div instead of nodeChart!
	$(".nodeChart").html("");
	$("#nodeTables").hide();

	$.getJSON("backend/settings", {})
	.done(function (data) {

		setStatus("Settings loaded.");
	})
	.fail(function (jqxhr, textStatus, error) {
		setError('Fetching settings failed! ('+error+')');
	})
}
