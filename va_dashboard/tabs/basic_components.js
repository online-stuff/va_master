var React = require('react');
var Bootstrap = require('react-bootstrap');
var Network = require('../network');

var Filter = React.createClass({

    filter: function(e){
        //this.props.handleChange(e.target.value);
        this.props.dispatch({type: 'FILTER', filterBy: e.target.value});
    },

    render: function () {
        return (
            <Bootstrap.InputGroup>
                <Bootstrap.FormControl
                    type="text"
                    placeholder="Filter"
                    value={this.props.table.filterBy}
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

    openModal: function() {
        this.props.dispatch({type: 'OPEN_MODAL'});
    },

    render: function () {
        var onclick = null, glyph;
        switch (this.props.action) {
            case "modal":
                onclick = this.openModal;
                break;
            default:
                onclick = null;
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


module.exports = {
    "Filter": Filter,
    "Button": Button,
    "Heading": Heading,
    "Paragraph": Paragraph
}
