"""
Payment Integration Module

This module provides Stripe payment integration for subscription management.
"""

import os
import logging
from datetime import datetime, timedelta
from flask import request, jsonify
import stripe
from database.database_manager import DatabaseManager
from database.models import User
from utils.auth import AuthManager

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY', 'sk_test_your_test_key')

# Subscription prices (create these in your Stripe dashboard)
SUBSCRIPTION_PRICES = {
    'pro': {
        'price_id': 'price_12345abc',  # Replace with actual Stripe price ID
        'amount': 5000000,  # 5M VND = $200
        'currency': 'vnd',
        'interval': 'month'
    },
    'enterprise': {
        'price_id': 'price_67890def',  # Replace with actual Stripe price ID
        'amount': 15000000,  # 15M VND = $600
        'currency': 'vnd',
        'interval': 'month'
    }
}


class PaymentManager:
    """Manages Stripe payments and subscriptions"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.auth_manager = AuthManager(db_manager)
    
    def create_checkout_session(self, user_id: int, tier: str):
        """
        Create Stripe checkout session for subscription
        
        Args:
            user_id: User ID
            tier: Subscription tier (pro, enterprise)
            
        Returns:
            dict with session ID and URL
        """
        try:
            if tier not in SUBSCRIPTION_PRICES:
                return {'error': 'Invalid tier'}, 400
            
            # Get user
            user = self.db_manager.get_user_by_id(user_id)
            if not user:
                return {'error': 'User not found'}, 404
            
            price_config = SUBSCRIPTION_PRICES[tier]
            
            # Create checkout session
            session = stripe.checkout.Session.create(
                customer_email=user.email,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_config['price_id'],
                    'quantity': 1
                }],
                mode='subscription',
                success_url=f"{os.getenv('BASE_URL', 'http://localhost:5000')}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{os.getenv('BASE_URL', 'http://localhost:5000')}/payment/cancel",
                metadata={
                    'user_id': user_id,
                    'tier': tier
                }
            )
            
            logger.info(f"Created checkout session for user {user_id}, tier {tier}")
            
            return {
                'session_id': session.id,
                'url': session.url
            }
            
        except Exception as e:
            logger.error(f"Error creating checkout session: {e}")
            return {'error': 'Payment setup failed'}, 500
    
    def handle_webhook(self, payload: bytes, sig_header: str):
        """
        Handle Stripe webhook events
        
        Args:
            payload: Raw webhook payload
            sig_header: Stripe signature header
            
        Returns:
            dict with status
        """
        try:
            webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET', 'whsec_your_webhook_secret')
            
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            
            # Handle different event types
            if event['type'] == 'checkout.session.completed':
                return self._handle_checkout_completed(event['data']['object'])
            elif event['type'] == 'invoice.payment_succeeded':
                return self._handle_payment_succeeded(event['data']['object'])
            elif event['type'] == 'invoice.payment_failed':
                return self._handle_payment_failed(event['data']['object'])
            elif event['type'] == 'customer.subscription.deleted':
                return self._handle_subscription_cancelled(event['data']['object'])
            
            logger.info(f"Unhandled webhook event: {event['type']}")
            return {'status': 'ignored'}
            
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return {'error': 'Webhook processing failed'}, 400
    
    def _handle_checkout_completed(self, session):
        """Handle successful checkout completion"""
        try:
            user_id = int(session['metadata']['user_id'])
            tier = session['metadata']['tier']
            
            # Update user subscription
            user = self.db_manager.get_user_by_id(user_id)
            if user:
                user.subscription_tier = tier
                user.subscription_expires = datetime.utcnow() + timedelta(days=30)
                
                # Store Stripe customer ID
                if 'customer' in session:
                    user.raw_data = str({
                        'stripe_customer_id': session['customer'],
                        'subscription_id': session.get('subscription')
                    })
                
                self.db_manager.update_user(user)
                
                logger.info(f"User {user_id} upgraded to {tier} tier")
                
                return {'status': 'success', 'user_id': user_id, 'tier': tier}
            
        except Exception as e:
            logger.error(f"Error handling checkout completion: {e}")
            return {'error': 'Failed to process checkout'}
    
    def _handle_payment_succeeded(self, invoice):
        """Handle successful payment"""
        try:
            subscription_id = invoice['subscription']
            # Extend user subscription
            # Implementation depends on your database structure
            
            logger.info(f"Payment succeeded for subscription {subscription_id}")
            return {'status': 'success'}
            
        except Exception as e:
            logger.error(f"Error handling payment success: {e}")
            return {'error': 'Failed to process payment'}
    
    def _handle_payment_failed(self, invoice):
        """Handle failed payment"""
        try:
            subscription_id = invoice['subscription']
            # Handle failed payment (downgrade user, send notification, etc.)
            
            logger.warning(f"Payment failed for subscription {subscription_id}")
            return {'status': 'handled'}
            
        except Exception as e:
            logger.error(f"Error handling payment failure: {e}")
            return {'error': 'Failed to process payment failure'}
    
    def _handle_subscription_cancelled(self, subscription):
        """Handle subscription cancellation"""
        try:
            # Find user by subscription ID and downgrade
            # Implementation depends on your database structure
            
            logger.info(f"Subscription cancelled: {subscription['id']}")
            return {'status': 'handled'}
            
        except Exception as e:
            logger.error(f"Error handling subscription cancellation: {e}")
            return {'error': 'Failed to process cancellation'}
    
    def cancel_subscription(self, user_id: int):
        """Cancel user subscription"""
        try:
            user = self.db_manager.get_user_by_id(user_id)
            if not user:
                return {'error': 'User not found'}, 404
            
            # Get subscription ID from user data
            raw_data = eval(user.raw_data) if user.raw_data else {}
            subscription_id = raw_data.get('subscription_id')
            
            if subscription_id:
                # Cancel in Stripe
                stripe.Subscription.modify(subscription_id, cancel_at_period_end=True)
                
                logger.info(f"Cancelled subscription {subscription_id} for user {user_id}")
                
                return {'message': 'Subscription cancelled successfully'}
            else:
                return {'error': 'No active subscription found'}, 404
                
        except Exception as e:
            logger.error(f"Error cancelling subscription: {e}")
            return {'error': 'Failed to cancel subscription'}, 500


# Flask route handlers
def create_subscription_handler():
    """Handle subscription creation"""
    try:
        data = request.get_json()
        
        if not data or 'tier' not in data:
            return jsonify({'error': 'Tier required'}), 400
        
        tier = data['tier']
        if tier not in ['pro', 'enterprise']:
            return jsonify({'error': 'Invalid tier'}), 400
        
        # Get current user
        from utils.auth import get_jwt_identity
        user_id = get_jwt_identity()
        
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Create payment manager
        db_manager = DatabaseManager()
        payment_manager = PaymentManager(db_manager)
        
        # Create checkout session
        result = payment_manager.create_checkout_session(user_id, tier)
        
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]
        else:
            return jsonify(result)
            
    except Exception as e:
        logger.error(f"Subscription creation error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


def webhook_handler():
    """Handle Stripe webhooks"""
    try:
        payload = request.data
        sig_header = request.headers.get('Stripe-Signature')
        
        if not sig_header:
            return jsonify({'error': 'Missing signature'}), 400
        
        # Create payment manager
        db_manager = DatabaseManager()
        payment_manager = PaymentManager(db_manager)
        
        # Process webhook
        result = payment_manager.handle_webhook(payload, sig_header)
        
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]
        else:
            return jsonify(result)
            
    except Exception as e:
        logger.error(f"Webhook handler error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


def cancel_subscription_handler():
    """Handle subscription cancellation"""
    try:
        # Get current user
        from utils.auth import get_jwt_identity
        user_id = get_jwt_identity()
        
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Create payment manager
        db_manager = DatabaseManager()
        payment_manager = PaymentManager(db_manager)
        
        # Cancel subscription
        result = payment_manager.cancel_subscription(user_id)
        
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]
        else:
            return jsonify(result)
            
    except Exception as e:
        logger.error(f"Subscription cancellation error: {e}")
        return jsonify({'error': 'Internal server error'}), 500