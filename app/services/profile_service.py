from sqlalchemy import func, desc
from app.extensions import db
from app.models.user import User
from app.models.review import Review
from app.models.order import Order
from app.models.writer_application import WriterApplication
from sqlalchemy import func, desc
from sqlalchemy.orm import aliased
from sqlalchemy import case
from sqlalchemy import func, desc, case, or_

def build_leaderboard(limit=None):
    subquery = (
        db.session.query(
            Review.reviewee_id.label("writer_id"),
            func.avg(Review.rating).label("avg_rating"),
        )
        .group_by(Review.reviewee_id)
        .subquery()
    )

    orders_count = func.count(Order.id)

    rating_col = case(
        (orders_count == 0, 5),
        else_=func.coalesce(subquery.c.avg_rating, 0)
    ).label("rating")

    q = (
        db.session.query(
            User.id,
            User.full_name,
            User.profile_image,
            WriterApplication.specialization,
            rating_col,
            orders_count.label("orders_completed"),
        )
        .join(WriterApplication, WriterApplication.user_id == User.id)
        .outerjoin(subquery, subquery.c.writer_id == User.id)
        .outerjoin(
            Order,
            (Order.writer_id == User.id) & (Order.status == "completed")
        )
        .filter(
            WriterApplication.status == "approved",
            or_(
                User.account_status == "paid_initial_deposit",
                User.application_status == "paid_initial_deposit"
            )
        )
        .group_by(
            User.id,
            User.full_name,
            User.profile_image,
            WriterApplication.specialization,
            subquery.c.avg_rating
        )
        .order_by(
            desc(rating_col),
            desc(orders_count),
            User.full_name
        )
    )

    if limit:
        q = q.limit(limit)

    return q.all()
