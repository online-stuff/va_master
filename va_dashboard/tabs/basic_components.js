var React = require('react');
var Bootstrap = require('react-bootstrap');
var Network = require('../network');

var Filter = React.createClass({

    filter: function(e){
        this.props.dispatch({type: 'FILTER', filterBy: e.target.value});
    },

    render: function () {
        return (
            <Bootstrap.InputGroup>
                <Bootstrap.FormControl
                    type="text"
                    placeholder="Filter"
                    value={this.props.filter.filterBy}
                    onChange={this.filter}
                    autoFocus
                />
                <Bootstrap.InputGroup.Addon>
                  <Bootstrap.Glyphicon glyph="search" />
                </Bootstrap.InputGroup.Addon>
            </Bootstrap.InputGroup>
        );
    }
});

var Button = React.createClass({

    shouldComponentUpdate: function(nextProps, nextState){
        return this.state != nextState;
    },

    openModal: function() {
        var modal = this.props.modalTemplate;
        this.props.dispatch({type: 'OPEN_MODAL', template: modal});
        var content = modal.content, data = {};
        for(j=0; j<content.length; j++){
            var html_elem = content[j];
            if(html_elem.type == "Form"){
                var elem = html_elem.elements;
                for(i=0; i<elem.length; i++){
                    if(elem[i].type !== 'label')
                        data[i] = elem[i].value;
                }
                this.props.dispatch({type: 'INIT_FORM', form_name: html_elem.name, form: data});
                break;
            }
        }
    },

    showTarget: function(target) {
        console.log(target);
        this.props.dispatch({type: 'TOGGLE'});
    },

    btn_action: function(action) {
        console.log(action);
    },

    render: function () {
        var onclick = null, glyph;
        switch (this.props.action) {
            case "modal":
                onclick = this.openModal;
                break;
            case "show":
                onclick = this.showTarget.bind(this, this.props.target);
                break;
            default:
                onclick = this.btn_action.bind(this, this.props.action);
        }
        if(this.props.hasOwnProperty('glyph')){
            glyph = <Bootstrap.Glyphicon glyph='plus' />;
        }
        return (
            <Bootstrap.Button onClick={onclick}>
                {glyph}
                {this.props.name}
            </Bootstrap.Button>
        );
    }
});

var Heading = React.createClass({

    render: function () {
        return (
            <h3>
                {this.props.name}
            </h3>
        );
    }
});

var Paragraph = React.createClass({

    render: function () {
        return (
            <div>
                {this.props.name}
            </div>
        );
    }
});

var Frame = React.createClass({

    render: function () {
        return (
            <iframe key={this.props.name} src={this.props.src} className="iframe"></iframe>
        );
    }
});


module.exports = {
    "Filter": Filter,
    "Button": Button,
    "Heading": Heading,
    "Paragraph": Paragraph,
    "Frame": Frame
}
