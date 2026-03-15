import json
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

class RestaurantAnalytics:
    def __init__(self, json_file=None):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        if json_file is None:
            json_file = os.path.join(current_dir, 'data', 'orders.json')
        
        self.json_file = json_file
        self.output_dir = os.path.join(current_dir, 'data')
        self.data = self.load_data()
        self.df = self.process_data()
        
    def load_data(self):
        """Load JSON data from file"""
        try:
            if not os.path.exists(self.json_file):
                print("[INFO] Data file not found, using empty dataset")
                return []
            
            with open(self.json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"[INFO] Loaded {len(data)} orders")
            return data
        except Exception as e:
            print(f"[ERROR] Error loading data: {str(e)}")
            return []
    
    def process_data(self):
        """Process data into DataFrame"""
        if not self.data:
            return pd.DataFrame()
        
        records = []
        for order in self.data:
            for item in order.get('items', []):
                try:
                    date_str = order.get('date', '')
                    if date_str:
                        try:
                            date_obj = datetime.strptime(date_str, '%d/%m/%Y, %I:%M:%S %p')
                        except:
                            try:
                                date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                            except:
                                date_obj = datetime.now()
                    else:
                        date_obj = datetime.now()
                except:
                    date_obj = datetime.now()
                
                records.append({
                    'bill_no': order.get('billNo', ''),
                    'table_no': order.get('tableNo', ''),
                    'customer': order.get('userName', 'Guest'),
                    'item_name': str(item.get('name', '')).strip().title(),
                    'item_price': float(item.get('price', 0)),
                    'quantity': int(item.get('quantity', 1)),
                    'item_total': float(item.get('totalPrice', 0)),
                    'order_total': float(order.get('total', 0)),
                    'payment_mode': order.get('paymentMode', 'Cash'),
                    'date': date_obj
                })
        
        if not records:
            return pd.DataFrame()
        
        df = pd.DataFrame(records)
        
        # Add derived columns
        df['day'] = df['date'].dt.date
        df['hour'] = df['date'].dt.hour
        df['day_of_week'] = df['date'].dt.day_name()
        df['week_number'] = df['date'].dt.isocalendar().week
        df['month'] = df['date'].dt.month
        df['year'] = df['date'].dt.year
        
        return df
    
    def generate_summary(self):
        """Generate summary statistics"""
        if self.df.empty:
            return {
                'total_orders': 0,
                'total_revenue': 0,
                'average_order_value': 0,
                'total_items_sold': 0,
                'unique_items': 0,
                'last_updated': datetime.now().isoformat(),
                'message': 'No data available for analytics'
            }
        
        # Get unique orders (by bill number)
        unique_orders = self.df[['bill_no', 'order_total']].drop_duplicates()
        
        total_orders = len(unique_orders)
        total_revenue = unique_orders['order_total'].sum()
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        total_items_sold = self.df['quantity'].sum()
        unique_items = self.df['item_name'].nunique()
        
        # Top item analysis
        item_stats = self.df.groupby('item_name').agg({
            'quantity': 'sum',
            'item_total': 'sum'
        }).reset_index()
        
        if not item_stats.empty:
            top_item_row = item_stats.loc[item_stats['item_total'].idxmax()]
            top_item = top_item_row['item_name']
            top_item_revenue = (top_item_row['item_total'] / total_revenue * 100) if total_revenue > 0 else 0
        else:
            top_item = None
            top_item_revenue = 0
        
        # Time-based analysis
        current_date = datetime.now()
        last_week_date = current_date - timedelta(days=7)
        
        current_week_data = self.df[self.df['date'] >= last_week_date]
        previous_week_data = self.df[
            (self.df['date'] >= last_week_date - timedelta(days=7)) & 
            (self.df['date'] < last_week_date)
        ]
        
        current_week_revenue = current_week_data['order_total'].sum() if not current_week_data.empty else 0
        previous_week_revenue = previous_week_data['order_total'].sum() if not previous_week_data.empty else 0
        
        revenue_growth = 0
        if previous_week_revenue > 0:
            revenue_growth = ((current_week_revenue - previous_week_revenue) / previous_week_revenue) * 100
        
        # Peak hour analysis
        hourly_sales = self.df.groupby('hour')['order_total'].sum()
        peak_hour = hourly_sales.idxmax() if not hourly_sales.empty else None
        
        return {
            'total_orders': total_orders,
            'total_revenue': round(total_revenue, 2),
            'average_order_value': round(avg_order_value, 2),
            'total_items_sold': int(total_items_sold),
            'unique_items': int(unique_items),
            'top_item': top_item,
            'top_item_revenue': round(top_item_revenue, 2) if top_item_revenue else 0,
            'current_week_revenue': round(current_week_revenue, 2),
            'revenue_growth': round(revenue_growth, 2),
            'peak_hour': int(peak_hour) if peak_hour else None,
            'last_updated': datetime.now().isoformat(),
            'data_range': {
                'start': self.df['date'].min().strftime('%Y-%m-%d'),
                'end': self.df['date'].max().strftime('%Y-%m-%d'),
                'days': (self.df['date'].max() - self.df['date'].min()).days + 1
            }
        }
    
    def generate_weekly_insights(self):
        """Generate weekly insights"""
        if self.df.empty:
            return {
                'message': 'No data available for weekly insights',
                'last_updated': datetime.now().isoformat()
            }
        
        current_date = datetime.now()
        current_week = current_date.isocalendar().week
        previous_week = current_week - 1 if current_week > 1 else 52
        
        # Current week data
        current_week_data = self.df[self.df['week_number'] == current_week]
        previous_week_data = self.df[self.df['week_number'] == previous_week]
        
        # Calculate metrics
        current_week_revenue = 0
        previous_week_revenue = 0
        
        if not current_week_data.empty:
            current_week_revenue = current_week_data[['bill_no', 'order_total']].drop_duplicates()['order_total'].sum()
        
        if not previous_week_data.empty:
            previous_week_revenue = previous_week_data[['bill_no', 'order_total']].drop_duplicates()['order_total'].sum()
        
        growth_percent = 0
        if previous_week_revenue > 0:
            growth_percent = ((current_week_revenue - previous_week_revenue) / previous_week_revenue) * 100
        
        # Best day and peak hour
        best_day = None
        peak_hour = None
        if not current_week_data.empty:
            best_day_data = current_week_data.groupby('day_of_week')['order_total'].sum()
            if not best_day_data.empty:
                best_day = best_day_data.idxmax()
            
            peak_hour_data = current_week_data.groupby('hour')['order_total'].sum()
            if not peak_hour_data.empty:
                peak_hour = int(peak_hour_data.idxmax())
        
        # Top items this week
        top_items = []
        if not current_week_data.empty:
            top_items_df = current_week_data.groupby('item_name').agg({
                'quantity': 'sum',
                'item_total': 'sum'
            }).nlargest(5, 'item_total')
            
            top_items = [
                {
                    'name': idx,
                    'quantity': int(row['quantity']),
                    'revenue': round(row['item_total'], 2)
                }
                for idx, row in top_items_df.iterrows()
            ]
        
        return {
            'current_week': current_week,
            'current_week_revenue': round(current_week_revenue, 2),
            'previous_week_revenue': round(previous_week_revenue, 2),
            'growth_percent': round(growth_percent, 2),
            'best_day': best_day,
            'peak_hour': peak_hour,
            'top_items': top_items,
            'last_updated': datetime.now().isoformat()
        }

def main():
    """Main function to run analytics"""
    print("=" * 60)
    print("STARTING RESTAURANT ANALYTICS")
    print("=" * 60)
    
    # Initialize analytics
    analytics = RestaurantAnalytics()
    
    # Generate summary
    summary = analytics.generate_summary()
    
    # Save summary to JSON file
    summary_path = os.path.join(analytics.output_dir, 'analytics_summary.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"[SUCCESS] Saved summary to {summary_path}")
    
    # Generate weekly insights
    weekly_insights = analytics.generate_weekly_insights()
    weekly_path = os.path.join(analytics.output_dir, 'weekly_insights.json')
    with open(weekly_path, 'w', encoding='utf-8') as f:
        json.dump(weekly_insights, f, indent=2, ensure_ascii=False)
    
    print(f"[SUCCESS] Saved weekly insights to {weekly_path}")
    
    # Print summary to console
    print("\n" + "=" * 60)
    print("ANALYTICS SUMMARY")
    print("=" * 60)
    print(f"Total Orders: {summary.get('total_orders', 0)}")
    print(f"Total Revenue: Rs.{summary.get('total_revenue', 0):,.2f}")
    print(f"Average Order Value: Rs.{summary.get('average_order_value', 0):,.2f}")
    print(f"Items Sold: {summary.get('total_items_sold', 0)}")
    
    if summary.get('top_item'):
        print(f"Top Item: {summary['top_item']} ({summary.get('top_item_revenue', 0):.1f}% of revenue)")
    
    if summary.get('data_range'):
        print(f"Data Range: {summary['data_range']['start']} to {summary['data_range']['end']}")
    
    print("=" * 60)
    print("ANALYTICS COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    main()