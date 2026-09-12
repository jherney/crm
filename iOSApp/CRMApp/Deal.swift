import Foundation
import CoreData

@objc(Deal)
public class Deal: NSManagedObject {
    @NSManaged public var id: UUID?
    @NSManaged public var name: String?
    @NSManaged public var value: Double
    @NSManaged public var stage: String?
    @NSManaged public var probability: Int16
    @NSManaged public var expectedCloseDate: Date?
    @NSManaged public var notes: String?
    @NSManaged public var createdAt: Date?
    @NSManaged public var updatedAt: Date?
    @NSManaged public var contact: Contact?
    @NSManaged public var company: Company?
    @NSManaged public var activities: NSSet?
}

extension Deal {
    @nonobjc public class func fetchRequest() -> NSFetchRequest<Deal> {
        return NSFetchRequest<Deal>(entityName: "Deal")
    }
    
    static let stages = ["Lead", "Qualified", "Proposal", "Negotiation", "Closed Won", "Closed Lost"]
    
    var formattedValue: String {
        let formatter = NumberFormatter()
        formatter.numberStyle = .currency
        formatter.currencyCode = "USD"
        return formatter.string(from: NSNumber(value: value)) ?? "$0.00"
    }
}