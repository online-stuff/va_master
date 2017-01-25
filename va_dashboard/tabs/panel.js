var React = require('react');
var Bootstrap = require('react-bootstrap');
var connect = require('react-redux').connect;
var Network = require('../network');
var ReactDOM = require('react-dom');
var widgets = require('./main_components');

var Panel = React.createClass({
    getInitialState: function () {
        return {
            template: {
                "title": "",
                "help_url": "",
                "content": []
            }
        };
    },

    getPanel: function (id, instance) {
        var me = this;
        var data = {'panel': id, 'instance_name': instance};
        console.log(data);
        Network.get('/api/panels/get_panel', this.props.auth.token, data).done(function (data) {
            me.setState({template: data});
        });
    },

    componentDidMount: function () {
        this.getPanel(this.props.params.id, this.props.params.instance);
    },

    componentWillReceiveProps: function (nextProps) {
        if (nextProps.params.id !== this.props.params.id || nextProps.params.instance !== this.props.params.instance) {
            this.getPanel(nextProps.params.id, nextProps.params.instance);
        }
    },

    componentWillUnmount: function () {
        this.props.dispatch({type: 'RESET_FILTER'});
    },

    render: function () {
        var redux = {};

        var elements = this.state.template.content.map(function(element) {
            element.key = element.name;
            if(Object.keys(redux).indexOf(element.type) < 0){
                var Component = widgets[element.type];
                redux[element.type] = connect(function(state){
                    var newstate = {auth: state.auth};
                    if(typeof element.reducers !== 'undefined'){
                        var r = element.reducers;
                        for (var i = 0; i < r.length; i++) {
                            newstate[r[i]] = state[r[i]];
                        }
                    }
                    return newstate;
                })(Component);
            }
            var Redux = redux[element.type];
            return React.createElement(Redux, element);
        });

        return (
            <div key={this.props.params.id}>
                <h1>{this.state.template.title}</h1>
                {elements}
            </div>
        );
    }

});

Panel = connect(function(state){
    return {auth: state.auth};
})(Panel);

module.exports = Panel;
