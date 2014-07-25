
function setStatus(id, text) {
	$(id)
	.parent()
	.find('.status')
	.addClass('normal')
	.removeClass('error')
	.html(text);
}

function setError(id, text) {
	$(id)
	.parent()
	.find('.status')
	.removeClass('normal')
	.addClass('error')
	.html(text);
}

// Print a node name with optional link
function nodeLink(node) {
	var re = /^[0-9.]+$/;
	if(node != "Internet" && !re.test(node)) {
		return "<a href='javascript:loadNode(\""+node+"\");'>"+node+"</a>";
	}
	return node;
}

