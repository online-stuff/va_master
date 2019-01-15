import React, { Component } from 'react';
var Bootstrap = require('react-bootstrap');
var classNames = require('classnames');
import { connect } from 'react-redux';
var Network = require('../network');
import { getSpinner } from './util';
import ReactJson from 'react-json-view'


class Integrations extends Component {
    constructor(props) {
        super(props);
        this.state = {
            loading: true,
        };
    }

    componentDidMount() {
        var me=this;
        me.setState({loading: false});
    }


    render() {
        var me=this;
        var loading = this.state.loading;
        return (
                <div>
                    {loading && getSpinner()}
                    <div style={this.props.style} className="card">
                        <div className="card-body">
                        <div>
                            <table className="table striped">
                                <thead>
                                    <tr className="reactable-filterer">
                                        <td colspan="1">
                                            <h4>Integrations</h4>
                                        </td>
                                        <td colspan="5" style={{textAlign: 'right'}}>                         
                                            <Bootstrap.Button>
                                                <Bootstrap.Glyphicon glyph='plus' />
                                                Create trigger
                                            </Bootstrap.Button>
                                        </td>
                                    </tr>
                                </thead>
                            </table>
                        </div>
                            <br/>
                        </div>
                    </div>
                </div>);
}
}

module.exports = connect(state => {
    return { auth: state.auth, alert: state.alert };
})(Integrations);