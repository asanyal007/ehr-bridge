"""
HL7 V2 Routing and Filtering Engine
Implements content-based routing similar to Rhapsody/Mirth Connect
"""
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import re
from hl7_parser_advanced import HL7MessageTree, get_hl7_advanced_parser


class RoutingRule:
    """Represents a single routing rule with conditions and actions"""
    
    def __init__(self, name: str, conditions: List[Dict], actions: List[Dict], priority: int = 100):
        self.name = name
        self.conditions = conditions  # List of condition dictionaries
        self.actions = actions        # List of action dictionaries
        self.priority = priority      # Lower number = higher priority
        self.enabled = True
        self.hit_count = 0
        self.last_executed = None
    
    def evaluate(self, message_tree: HL7MessageTree) -> bool:
        """Evaluate all conditions against the message tree"""
        if not self.enabled:
            return False
        
        # All conditions must be true (AND logic)
        for condition in self.conditions:
            if not self._evaluate_condition(condition, message_tree):
                return False
        
        self.hit_count += 1
        self.last_executed = datetime.now()
        return True
    
    def _evaluate_condition(self, condition: Dict, message_tree: HL7MessageTree) -> bool:
        """Evaluate a single condition"""
        condition_type = condition.get('type', 'xpath')
        
        if condition_type == 'xpath':
            return self._evaluate_xpath_condition(condition, message_tree)
        elif condition_type == 'segment_exists':
            return self._evaluate_segment_exists(condition, message_tree)
        elif condition_type == 'message_type':
            return self._evaluate_message_type(condition, message_tree)
        elif condition_type == 'custom':
            return self._evaluate_custom_condition(condition, message_tree)
        
        return False
    
    def _evaluate_xpath_condition(self, condition: Dict, message_tree: HL7MessageTree) -> bool:
        """Evaluate XPath-based condition"""
        xpath = condition.get('xpath', '')
        operator = condition.get('operator', 'equals')
        value = condition.get('value', '')
        
        actual_value = str(message_tree.xpath(xpath) or '')
        
        if operator == 'equals':
            return actual_value == value
        elif operator == 'contains':
            return value.lower() in actual_value.lower()
        elif operator == 'starts_with':
            return actual_value.lower().startswith(value.lower())
        elif operator == 'regex':
            return bool(re.match(value, actual_value))
        elif operator == 'not_empty':
            return bool(actual_value.strip())
        elif operator == 'empty':
            return not bool(actual_value.strip())
        
        return False
    
    def _evaluate_segment_exists(self, condition: Dict, message_tree: HL7MessageTree) -> bool:
        """Check if segment exists"""
        segment_type = condition.get('segment', '')
        return message_tree.get_segment(segment_type) is not None
    
    def _evaluate_message_type(self, condition: Dict, message_tree: HL7MessageTree) -> bool:
        """Check message type"""
        expected_type = condition.get('messageType', '')
        return message_tree.message_type == expected_type
    
    def _evaluate_custom_condition(self, condition: Dict, message_tree: HL7MessageTree) -> bool:
        """Evaluate custom JavaScript-like condition"""
        # Placeholder for custom scripting
        script = condition.get('script', '')
        # In a full implementation, this would execute JavaScript
        # For now, return True as placeholder
        return True
    
    def execute_actions(self, message_tree: HL7MessageTree, context: Dict) -> List[Dict]:
        """Execute all actions for this rule"""
        results = []
        
        for action in self.actions:
            result = self._execute_action(action, message_tree, context)
            results.append(result)
        
        return results
    
    def _execute_action(self, action: Dict, message_tree: HL7MessageTree, context: Dict) -> Dict:
        """Execute a single action"""
        action_type = action.get('type', 'route')
        
        if action_type == 'route':
            return self._route_message(action, message_tree, context)
        elif action_type == 'transform':
            return self._transform_message(action, message_tree, context)
        elif action_type == 'log':
            return self._log_message(action, message_tree, context)
        elif action_type == 'filter':
            return self._filter_message(action, message_tree, context)
        
        return {'type': action_type, 'status': 'unknown_action'}
    
    def _route_message(self, action: Dict, message_tree: HL7MessageTree, context: Dict) -> Dict:
        """Route message to destination"""
        destination = action.get('destination', 'default')
        return {
            'type': 'route',
            'status': 'success',
            'destination': destination,
            'messageId': message_tree.message_control_id
        }
    
    def _transform_message(self, action: Dict, message_tree: HL7MessageTree, context: Dict) -> Dict:
        """Apply transformation"""
        transformation = action.get('transformation', 'pass_through')
        return {
            'type': 'transform',
            'status': 'success',
            'transformation': transformation
        }
    
    def _log_message(self, action: Dict, message_tree: HL7MessageTree, context: Dict) -> Dict:
        """Log message"""
        log_level = action.get('level', 'info')
        message = action.get('message', f'Message {message_tree.message_control_id} processed')
        
        print(f"[{log_level.upper()}] {message}")
        
        return {
            'type': 'log',
            'status': 'success',
            'level': log_level,
            'message': message
        }
    
    def _filter_message(self, action: Dict, message_tree: HL7MessageTree, context: Dict) -> Dict:
        """Filter/block message"""
        reason = action.get('reason', 'Filtered by rule')
        return {
            'type': 'filter',
            'status': 'blocked',
            'reason': reason
        }


class Channel:
    """Represents a communication channel with routing rules"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.rules = []
        self.enabled = True
        self.message_count = 0
        self.error_count = 0
        self.last_message_time = None
        
        # Channel configuration
        self.source_connector = None
        self.destination_connectors = []
        self.pre_processors = []
        self.post_processors = []
    
    def add_rule(self, rule: RoutingRule):
        """Add routing rule to channel"""
        self.rules.append(rule)
        # Sort by priority (lower number = higher priority)
        self.rules.sort(key=lambda r: r.priority)
    
    def process_message(self, hl7_message: str, context: Dict = None) -> Dict[str, Any]:
        """Process HL7 message through channel rules"""
        if not self.enabled:
            return {'status': 'channel_disabled', 'results': []}
        
        context = context or {}
        self.message_count += 1
        self.last_message_time = datetime.now()
        
        try:
            # Parse message
            parser = get_hl7_advanced_parser()
            message_tree = parser.parse_message(hl7_message)
            
            # Check for parsing errors
            if message_tree.errors:
                self.error_count += 1
                return {
                    'status': 'parse_error',
                    'errors': message_tree.errors,
                    'results': []
                }
            
            # Process through rules
            results = []
            matched_rules = []
            
            for rule in self.rules:
                if rule.evaluate(message_tree):
                    matched_rules.append(rule.name)
                    rule_results = rule.execute_actions(message_tree, context)
                    results.extend(rule_results)
            
            return {
                'status': 'success',
                'messageType': message_tree.message_type,
                'messageId': message_tree.message_control_id,
                'matchedRules': matched_rules,
                'results': results,
                'processingTime': datetime.now()
            }
        
        except Exception as e:
            self.error_count += 1
            return {
                'status': 'processing_error',
                'error': str(e),
                'results': []
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get channel processing statistics"""
        return {
            'name': self.name,
            'enabled': self.enabled,
            'messageCount': self.message_count,
            'errorCount': self.error_count,
            'successRate': (self.message_count - self.error_count) / max(self.message_count, 1),
            'lastMessageTime': self.last_message_time.isoformat() if self.last_message_time else None,
            'ruleCount': len(self.rules),
            'ruleHits': [
                {
                    'name': rule.name,
                    'hitCount': rule.hit_count,
                    'lastExecuted': rule.last_executed.isoformat() if rule.last_executed else None
                }
                for rule in self.rules
            ]
        }


class RoutingEngine:
    """
    Main HL7 V2 Routing Engine
    Manages channels and routing logic
    """
    
    def __init__(self):
        self.channels = {}
        self.global_filters = []
        self.message_history = []
        self.max_history = 1000
    
    def create_channel(self, name: str, description: str = "") -> Channel:
        """Create new routing channel"""
        channel = Channel(name, description)
        self.channels[name] = channel
        return channel
    
    def get_channel(self, name: str) -> Optional[Channel]:
        """Get channel by name"""
        return self.channels.get(name)
    
    def process_message(self, hl7_message: str, channel_name: str, context: Dict = None) -> Dict[str, Any]:
        """Process message through specific channel"""
        channel = self.get_channel(channel_name)
        if not channel:
            return {'status': 'channel_not_found', 'channel': channel_name}
        
        # Add to message history
        self._add_to_history({
            'timestamp': datetime.now(),
            'channel': channel_name,
            'messagePreview': hl7_message[:100] + '...' if len(hl7_message) > 100 else hl7_message
        })
        
        return channel.process_message(hl7_message, context)
    
    def broadcast_message(self, hl7_message: str, context: Dict = None) -> Dict[str, List[Dict]]:
        """Broadcast message to all enabled channels"""
        results = {}
        
        for channel_name, channel in self.channels.items():
            if channel.enabled:
                result = channel.process_message(hl7_message, context)
                results[channel_name] = result
        
        return results
    
    def get_engine_statistics(self) -> Dict[str, Any]:
        """Get overall engine statistics"""
        total_messages = sum(ch.message_count for ch in self.channels.values())
        total_errors = sum(ch.error_count for ch in self.channels.values())
        
        return {
            'channelCount': len(self.channels),
            'activeChannels': len([ch for ch in self.channels.values() if ch.enabled]),
            'totalMessages': total_messages,
            'totalErrors': total_errors,
            'overallSuccessRate': (total_messages - total_errors) / max(total_messages, 1),
            'channels': [ch.get_statistics() for ch in self.channels.values()],
            'messageHistoryCount': len(self.message_history)
        }
    
    def _add_to_history(self, entry: Dict):
        """Add entry to message history"""
        self.message_history.append(entry)
        
        # Maintain max history size
        if len(self.message_history) > self.max_history:
            self.message_history = self.message_history[-self.max_history:]
    
    def create_sample_channels(self):
        """Create sample channels for demonstration"""
        
        # Channel 1: ADT Messages to EHR
        adt_channel = self.create_channel('ADT_to_EHR', 'Route ADT messages to EHR system')
        
        adt_rule = RoutingRule(
            name='ADT_A01_A08_Filter',
            conditions=[
                {
                    'type': 'message_type',
                    'messageType': 'ADT^A01'
                }
            ],
            actions=[
                {
                    'type': 'log',
                    'level': 'info',
                    'message': 'Processing ADT A01 message'
                },
                {
                    'type': 'route',
                    'destination': 'EHR_System'
                }
            ],
            priority=10
        )
        adt_channel.add_rule(adt_rule)
        
        # Channel 2: Lab Results to Analytics
        lab_channel = self.create_channel('Lab_to_Analytics', 'Route lab results to analytics')
        
        lab_rule = RoutingRule(
            name='ORU_Lab_Results',
            conditions=[
                {
                    'type': 'message_type',
                    'messageType': 'ORU^R01'
                },
                {
                    'type': 'segment_exists',
                    'segment': 'OBX'
                }
            ],
            actions=[
                {
                    'type': 'transform',
                    'transformation': 'lab_to_fhir'
                },
                {
                    'type': 'route',
                    'destination': 'Analytics_DB'
                }
            ],
            priority=20
        )
        lab_channel.add_rule(lab_rule)
        
        # Channel 3: Error Handler
        error_channel = self.create_channel('Error_Handler', 'Handle malformed messages')
        
        error_rule = RoutingRule(
            name='Catch_All_Errors',
            conditions=[
                {
                    'type': 'xpath',
                    'xpath': 'MSH.9',
                    'operator': 'not_empty'
                }
            ],
            actions=[
                {
                    'type': 'log',
                    'level': 'warn',
                    'message': 'Message processed by error handler'
                },
                {
                    'type': 'route',
                    'destination': 'Error_Queue'
                }
            ],
            priority=1000  # Low priority (catch-all)
        )
        error_channel.add_rule(error_rule)


# Global routing engine instance
routing_engine = None

def get_routing_engine() -> RoutingEngine:
    """Get or create routing engine singleton"""
    global routing_engine
    if routing_engine is None:
        routing_engine = RoutingEngine()
        routing_engine.create_sample_channels()
    return routing_engine
