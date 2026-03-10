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

from sqlalchemy import func, desc, case, or_
from app.extensions import db
from app.models.user import User
from app.models.review import Review
from app.models.order import Order
from app.models.writer_application import WriterApplication


def build_leaderboard(limit=None):

    review_subq = (
        db.session.query(
            Review.reviewee_id.label("writer_id"),
            func.avg(Review.rating).label("avg_rating"),
        )
        .group_by(Review.reviewee_id)
        .subquery()
    )

    completed_orders = func.sum(
        case((Order.status == "completed", 1), else_=0)
    ).label("completed_orders")

    cancelled_orders = func.sum(
        case((Order.status == "cancelled", 1), else_=0)
    ).label("cancelled_orders")

    total_assigned = func.sum(
        case((Order.status.in_(["completed", "cancelled"]), 1), else_=0)
    ).label("total_assigned")

    rating_col = case(
        (completed_orders == 0, 5),
        else_=func.coalesce(review_subq.c.avg_rating, 0)
    ).label("rating")

    q = (
        db.session.query(
            User.id,
            User.full_name,
            User.profile_image,
            WriterApplication.specialization,
            rating_col,
            completed_orders,
            cancelled_orders,
            total_assigned,
        )
        .join(WriterApplication, WriterApplication.user_id == User.id)
        .outerjoin(review_subq, review_subq.c.writer_id == User.id)
        .outerjoin(Order, Order.writer_id == User.id)
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
            review_subq.c.avg_rating
        )
        .order_by(
            desc(rating_col),
            desc(completed_orders),
            User.full_name
        )
    )

    if limit:
        q = q.limit(limit)

    return q.all()
