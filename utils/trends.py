"""
Price Trend Analysis Module

This module provides price trend analysis functionality using basic ML techniques.
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database.models import PropertyListing, Base
from database.database_manager import DatabaseManager
import logging

logger = logging.getLogger(__name__)


class PriceTrendAnalyzer:
    """Analyzes price trends and identifies deals"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def calculate_price_trends(self, days_back=30):
        """
        Calculate price trends for each location
        
        Args:
            days_back: Number of days to look back for trend analysis
            
        Returns:
            dict: Trends data for each location
        """
        try:
            # Get data from database
            engine = self.db_manager.engine
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            query = f"""
                SELECT timestamp, location, price_per_m2 
                FROM property_listings 
                WHERE timestamp >= '{cutoff_date.isoformat()}'
                ORDER BY timestamp
            """
            
            df = pd.read_sql(query, engine)
            
            if df.empty:
                logger.warning("No data found for trend analysis")
                return {}
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            trends = {}
            
            # Calculate trends for each location
            for loc, group in df.groupby('location'):
                if len(group) > 2:  # Need at least 3 data points
                    try:
                        # Convert timestamps to days since first listing
                        first_date = group['timestamp'].min()
                        days = (group['timestamp'] - first_date).dt.days.values.reshape(-1, 1)
                        y = group['price_per_m2'].values
                        
                        # Add constant for intercept
                        X = sm.add_constant(days)
                        
                        # Fit OLS model
                        model = sm.OLS(y, X).fit()
                        
                        trends[loc] = {
                            'slope': float(model.params[1]),
                            'intercept': float(model.params[0]),
                            'p_value': float(model.pvalues[1]),
                            'r_squared': float(model.rsquared),
                            'data_points': len(group),
                            'avg_price': float(group['price_per_m2'].mean()),
                            'std_price': float(group['price_per_m2'].std())
                        }
                        
                        logger.info(f"Trend calculated for {loc}: slope={trends[loc]['slope']:.2f}, R²={trends[loc]['r_squared']:.3f}")
                        
                    except Exception as e:
                        logger.error(f"Error calculating trend for {loc}: {e}")
                        continue
            
            return trends
            
        except Exception as e:
            logger.error(f"Error in calculate_price_trends: {e}")
            return {}
    
    def flag_deals(self, deal_threshold=0.8):
        """
        Flag listings as deals based on price comparison
        
        Args:
            deal_threshold: Threshold below average to consider a deal (0.8 = 80% of avg)
        """
        try:
            # Get average prices by location
            engine = self.db_manager.engine
            avg_query = """
                SELECT location, AVG(price_per_m2) as avg_price, COUNT(*) as count
                FROM property_listings 
                GROUP BY location
                HAVING COUNT(*) >= 5
            """
            
            avg_df = pd.read_sql(avg_query, engine)
            avg_prices = dict(zip(avg_df['location'], avg_df['avg_price']))
            
            # Get all listings
            session = Session(engine)
            listings = session.query(PropertyListing).all()
            
            deals_found = 0
            for listing in listings:
                avg_price = avg_prices.get(listing.location)
                if avg_price:
                    # Check if this is a deal
                    if listing.price_per_m2 < avg_price * deal_threshold:
                        # Add deal flag to raw_data
                        raw_data = {}
                        if listing.raw_data:
                            try:
                                raw_data = eval(listing.raw_data) if isinstance(listing.raw_data, str) else listing.raw_data
                            except:
                                raw_data = {}
                        
                        raw_data['is_deal'] = True
                        raw_data['deal_score'] = round((avg_price - listing.price_per_m2) / avg_price * 100, 1)
                        raw_data['avg_price_location'] = avg_price
                        
                        listing.raw_data = str(raw_data)
                        deals_found += 1
                    else:
                        # Remove deal flag if exists
                        raw_data = {}
                        if listing.raw_data:
                            try:
                                raw_data = eval(listing.raw_data) if isinstance(listing.raw_data, str) else listing.raw_data
                            except:
                                raw_data = {}
                        
                        if 'is_deal' in raw_data:
                            del raw_data['is_deal']
                            del raw_data['deal_score']
                            del raw_data['avg_price_location']
                            listing.raw_data = str(raw_data)
            
            session.commit()
            session.close()
            
            logger.info(f"Flagged {deals_found} deals out of {len(listings)} listings")
            return deals_found
            
        except Exception as e:
            logger.error(f"Error in flag_deals: {e}")
            return 0
    
    def get_trend_summary(self):
        """Get a summary of current market trends"""
        trends = self.calculate_price_trends()
        
        if not trends:
            return {"message": "No trend data available"}
        
        # Calculate overall market direction
        slopes = [t['slope'] for t in trends.values()]
        avg_slope = np.mean(slopes)
        
        # Count locations with positive/negative trends
        positive_trends = sum(1 for slope in slopes if slope > 0)
        negative_trends = sum(1 for slope in slopes if slope < 0)
        
        # Find best and worst performing locations
        best_location = max(trends.items(), key=lambda x: x[1]['slope'])
        worst_location = min(trends.items(), key=lambda x: x[1]['slope'])
        
        return {
            "market_direction": "up" if avg_slope > 0 else "down",
            "avg_slope": round(avg_slope, 2),
            "locations_analyzed": len(trends),
            "positive_trends": positive_trends,
            "negative_trends": negative_trends,
            "best_performing": {
                "location": best_location[0],
                "slope": round(best_location[1]['slope'], 2),
                "r_squared": round(best_location[1]['r_squared'], 3)
            },
            "worst_performing": {
                "location": worst_location[0],
                "slope": round(worst_location[1]['slope'], 2),
                "r_squared": round(worst_location[1]['r_squared'], 3)
            },
            "trends_by_location": trends
        }


def run_trend_analysis():
    """Run trend analysis and flag deals"""
    try:
        db_manager = DatabaseManager()
        analyzer = PriceTrendAnalyzer(db_manager)
        
        # Calculate trends
        trends = analyzer.calculate_price_trends()
        logger.info(f"Calculated trends for {len(trends)} locations")
        
        # Flag deals
        deals_found = analyzer.flag_deals()
        logger.info(f"Flagged {deals_found} deals")
        
        # Get summary
        summary = analyzer.get_trend_summary()
        logger.info(f"Market direction: {summary['market_direction']}")
        
        return {
            "trends": trends,
            "deals_found": deals_found,
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"Error in run_trend_analysis: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    # Test the trend analysis
    result = run_trend_analysis()
    print("Trend Analysis Result:", result)