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
            showModal: false,
            stepIndex: -1
        };
        this.openTriggerModal=this.openTriggerModal.bind(this);
        this.closeModal=this.closeModal.bind(this);
        this.nextStep=this.nextStep.bind(this);
    }

    componentDidMount() {
        var me=this;
        me.setState({loading: false});
    }

    openTriggerModal(){
        this.setState({showModal: true});
    }

    closeModal(){
        this.setState({showModal: false});
    }

    nextStep(){
        this.setState({stepIndex: this.state.stepIndex+1});
    }

    render() {
        var me=this;
        var loading = this.state.loading;
        return (
                <div>
                    {loading && getSpinner()}
                    <div style={this.props.style} className="card">
                        <div className="card-body">
                            <table className="table striped">
                                <thead>
                                    <tr className="reactable-filterer">
                                        <td>
                                            <h4>Integrations</h4>
                                        </td>
                                        <td style={{textAlign: 'right'}}>                         
                                            <Bootstrap.Button onClick={()=> this.openTriggerModal()}>
                                                <Bootstrap.Glyphicon glyph='plus' />
                                                Create trigger
                                            </Bootstrap.Button>
                                        </td>
                                    </tr>
                                </thead>
                            </table>

                            <Bootstrap.Modal show={this.state.showModal} onHide={this.closeModal}>

                                <Bootstrap.Modal.Body>
                                    <Bootstrap.Tabs id="tabs">
                                        <Bootstrap.Tab eventKey={1} title="App 1">
                                            <h4>Choose App1</h4>
                                        </Bootstrap.Tab>
                                        <Bootstrap.Tab eventKey={2} title="App 2">
                                            <h4>Choose App2</h4>
                                        </Bootstrap.Tab>
                                        <Bootstrap.Tab eventKey={3} title="App 3">
                                            <h4>Arguments</h4>
                                        </Bootstrap.Tab>
                                    </Bootstrap.Tabs>
                                
                                </Bootstrap.Modal.Body>

                                <Bootstrap.Modal.Footer>
                                    <Bootstrap.ButtonGroup>
                                        <Bootstrap.Button bsStyle='primary' onClick={this.nextStep}>
                                            <Bootstrap.Glyphicon glyph='menu-right'></Bootstrap.Glyphicon> Next step</Bootstrap.Button>
                                        <Bootstrap.Button bsStyle='primary' onClick={this.nextStep}>
                                            <Bootstrap.Glyphicon glyph='menu-right'></Bootstrap.Glyphicon> Next step</Bootstrap.Button>
                                    </Bootstrap.ButtonGroup>
                                </Bootstrap.Modal.Footer>

                            </Bootstrap.Modal>

                            <br/>
                        </div>
                    </div>
                </div>);
}
}

module.exports = connect(state => {
    return { auth: state.auth, alert: state.alert };
})(Integrations);