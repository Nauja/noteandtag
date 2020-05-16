$(document).ready(function() {
	let body = $("body");
	let api_base_url = body.attr("data-api-base-url");
	let cdn_url = body.attr("data-cdn-url");
	
	let tags_div = $("#nat-tags");

	function query_tags(success, error) {
		$.ajax({
			url: api_base_url + "tags",
			type: "GET",
			contentType: "application/json",
			dataType: "json",
			success: function(response) {
				if (response["result"] != "Ok")
				{
					error(response["error"]);
				}
				else
				{
					success(response["params"]);
				}
			}
		});
	}
	
	function refresh_tags(data)
	{
		tags_div.html("");
		data.forEach(tag => {
			let p = $("<p>", {'class': 'nat-tag'});
			p.text(tag["name"] + ": " + tag["total"]);
			tags_div.append(p);
		});
	}
	
	query_tags(refresh_tags, () => {});
});
