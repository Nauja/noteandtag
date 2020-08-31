$(document).ready(function() {
	let body = $("body");
	let api_base_url = body.attr("data-api-base-url");
	let cdn_url = body.attr("data-cdn-url");
	
	function setHeight(jq_in){
	    jq_in.each(function(index, elem){
	        // This line will work with pure Javascript (taken from NicB's answer):
	        elem.style.height = elem.scrollHeight+'px'; 
	    });
	}

	var TagsUI = function(root, api_base_url) {
		this._root = root
		this._root.html("");
		this._api_base_url = api_base_url
		this._selection_changed = $.Callbacks();
	};
	
	TagsUI.prototype = {
		selection_changed: function(cb)
		{
			this._selection_changed.add(cb);
		},
		_on_tag_clicked: function(name)
		{
			this._root.find(`.nat-tag[data-name='${name}']`).toggleClass("nat-tag-selected");
			let tags = $.makeArray(this._root.find(".nat-tag-selected .nat-tag-name"));
			this._selection_changed.fire(tags.map(o => $(o).text()));
		},
		_display: function(tags)
		{
			this._root.html("");
			tags.forEach(tag => {
				let element = $("<a>", {'class': 'nat-tag', 'href': '#', 'data-name': tag["name"]}).append(
					$("<span>", {'class': 'nat-tag-name', 'text': tag["name"]}),
					$("<span>", {'class': 'nat-tag-total', 'text': tag["total"]}),
				);
				element.click(() => this._on_tag_clicked(tag["name"]));
				this._root.append(element);
			});
		},
		query: function() {
			$.ajax({
				url: this._api_base_url + "tags",
				type: "GET",
				contentType: "application/json",
				dataType: "json",
				success: (response) => {
					if (response["result"] != "Ok")
					{
						console.log(response["error"]);
					}
					else
					{
						this._display(response["params"]);
					}
				}
			});
		}
	};

	var NoteEditor = function(data, create) {
		this.root = $("<div>", {'class': 'nat-note-editor'}).append(
			$("<div>", {'class': 'nat-note-editor-body'}).append(
				$("<form>", {}).append(
					$("<input>", {'class': 'nat-note-editor-form-label', 'text': '', 'placeholder': 'Add a title...'}),
					$("<input>", {'class': 'nat-note-editor-form-author', 'text': '', 'placeholder': 'Add an author...'}),
					$("<textarea>", {'class': 'nat-note-editor-form-body', 'text': '', 'rows': '5', 'placeholder': 'Write note body here...'})
				),
				$("<div>", {'class': 'nat-note-editor-toolbar'}).append(
					$("<input>", {'type': 'button', 'class': 'nat-note-editor-save', 'value': "Save"}),
					$("<input>", {'type': 'button', 'class': 'nat-note-editor-cancel', 'value': "Cancel"}),
					$("<div>", {'style': 'clear: both;'})
				)
			)
		);
		this._create = create;
		this._cancelled = $.Callbacks();
		this._saved = $.Callbacks();
		this._widgets = {
			form: {
				label: this.root.find(".nat-note-editor-form-label").first(),
				author: this.root.find(".nat-note-editor-form-author").first(),
				body: this.root.find(".nat-note-editor-form-body").first()
			},
			cancel: this.root.find(".nat-note-editor-cancel").first(),
			save: this.root.find(".nat-note-editor-save").first()
		};
		this._widgets.form.body.change(() => this._resize_textarea());
		this._widgets.form.body.keyup(() => this._resize_textarea());
		this._widgets.form.body.keydown(() => this._resize_textarea());
		if (this._create === true) {
			this._widgets.cancel.addClass("nat-hidden");
			this._widgets.save.val("Add");
		} else {
			this._widgets.cancel.click(() => this._on_cancel_clicked());
		}
		this._widgets.save.click(() => this._on_save_clicked());
		this.update(data);
	};
	
	NoteEditor.prototype = {
		_on_save_clicked: function() {
			// Split yaml part and body part
			let parts = this._widgets.textarea.val().split("---\n");
			if (parts.length != 2)
			{
				this._show_error(true);
				return;
			}

			// Validate yaml part
			let new_data = {};
			try {
				new_data = jsyaml.load(parts[0]);
			} catch(error) {
				this._show_error(true);
				console.error(error);
				return;
			}

			// Send request
			this._show_error(false);
			new_data["body"] = parts[1];
		    let type = null;
		    let url = null;
		    if (this._create) {
		    	type = "PUT";
		    	url = api_base_url + "notes";
		    } else {
		    	type = "POST";
		    	new_data["id"] = this._data["id"];
		    	url = api_base_url + "notes/" + new_data["id"];
		    }

			$.ajax({
				url: url,
				type: type,
				contentType: "application/json",
				dataType: "json",
				data: JSON.stringify({"data": new_data}),
				success: (response) => {
					if (response["result"] != "Ok")
					{
						alert(response["error"]);
					}
					else
					{
						new_data = response["params"];
						this._saved.fire(new_data);
					}
				}
			});
		},
		_on_cancel_clicked: function() {
			this._cancelled.fire();
		},
		_resize_textarea: function() {
			this._widgets.form.body.css("height", this._widgets.form.body.prop("scrollHeight")+'px');
		},
		_show_error: function(val) {
			if (val) {
				this.root.addClass("nat-error");
				this.root.effect("shake");
			} else {
				this.root.removeClass("nat-error");
			}
		},
		update: function(data) {
			this._data = data;
			if (data) {
				console.log(data);
				this._widgets.form.body.text(data["body"]);
				this._widgets.form.label.val(data["label"]);
				this._widgets.form.author.val(data["author"]);
			} else {
				this._widgets.form.body.text("");
				this._widgets.form.label.val("");
				this._widgets.form.author.val("");
			}
		},
		cancelled: function(cb) {
			this._cancelled.add(cb);
		},
		saved: function(cb) {
			this._saved.add(cb);
		}
	};

	var NoteUI = function(data) {
		this.root = $("<div>", {'class': 'nat-note', 'data-id': ''}).append(
			$("<div>", {'class': 'nat-note-head'}).append(
				$("<span>", {'class': 'nat-note-label', 'text': ''}),
				$("<div>", {'class': 'nat-note-toolbar'}).append(
					$("<button>", {'class': 'nat-note-edit', 'type': 'button'}).append(
						$("<img>", {'src': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/OOjs_UI_icon_edit-ltr.svg/20px-OOjs_UI_icon_edit-ltr.svg.png'})
					)
				)
			),
			$("<div>", {'class': 'nat-note-body', 'text': ''}),
		);
		this._edit = $.Callbacks();
		this._widgets = {
			label: this.root.find(".nat-note-label").first(),
			body: this.root.find(".nat-note-body").first(),
			edit: this.root.find(".nat-note-edit").first()
		};
		this._widgets.edit.click(() => this._edit.fire());
		this.update(data);
	};
	
	NoteUI.prototype = {
		edit: function(cb) {
			this._edit.add(cb);
		},
		hide: function() {
			this.root.addClass("nat-hidden");
		},
		show: function() {
			this.root.removeClass("nat-hidden");
		},
		update: function(data) {
			this.root.attr("data-id", data["id"]);
			this._widgets.label.html(data["label"]);
			var conv = new showdown.Converter();
			conv.setFlavor('github');
			this._widgets.body.html(conv.makeHtml(data["body"]));
			this.data = data;
		}
	};

	var NotesUI = function(root, api_base_url) {
		this._root = root
		this._root.html("");
		this._changed = $.Callbacks();
		this._widgets = {
			editor: new NoteEditor(null, true),
			notes: []
		};
		this._widgets.editor.saved((data) => this._on_note_added(data));
		this._root.append(this._widgets.editor.root);
		this._api_base_url = api_base_url
	};
	
	NotesUI.prototype = {
		_display: function(notes)
		{
			this._widgets.notes.forEach(note => {
				note.root.remove();
			});
			this._widgets.notes = []
			notes.forEach(data => this._on_note_added(data));
		},
		_on_edit: function(note) {
			let editor = new NoteEditor(note.data);
			editor.saved((data) => this._on_note_edited(note, editor, data));
			editor.cancelled(() => this._on_edit_cancelled(note, editor));
			editor.root.insertBefore(note.root);
			note.hide();
		},
		_on_edit_cancelled: function(note, editor) {
			editor.root.remove();
			note.show();
		},
		_on_note_edited: function(note, editor, data) {
			editor.root.remove();
			note.update(data);
			note.show();
			this._changed.fire();
		},
		_on_note_added: function(data) {
			let widget = new NoteUI(data);
			widget.edit(() => this._on_edit(widget));
			this._widgets.notes.push(widget);
			widget.root.insertAfter(this._widgets.editor.root);
			this._changed.fire();
		},
		changed: function(cb) {
			this._changed.add(cb);
		},
		query: function(tags) {
			let url = this._api_base_url + "notes/"
			console.log(tags);
			if (tags !== undefined) {
				url += tags.join(":");
			}
	
			$.ajax({
				url: url,
				type: "GET",
				contentType: "application/json",
				dataType: "json",
				success: (response) => {
					if (response["result"] != "Ok")
					{
						console.log(response["error"]);
					}
					else
					{
						this._display(response["params"]);
					}
				}
			});
		}
	};

	let notes = new NotesUI($("#nat-notes"), api_base_url);
	let tags = new TagsUI($("#nat-tags"), api_base_url);

	notes.changed(() => tags.query());
	tags.selection_changed((tags) => notes.query(tags));
	tags.query();
	notes.query();
});
